import { replaceUndefinedAttributes, setMountedApp, getElement } from "./elements.js";
import { renderRecursively } from "./render.js";
import { ack, createRandomUUID, TAB_ID, OLD_TAB_ID } from "./utils.js";
import { logAndEmit } from "./utils.js";
import { runJavascript, download } from "./utils.js";

let app = undefined;

// Export getter for app so render.js can access it
export function getApp() {
  return app;
}

export function createApp(elements, options) {
  Object.entries(elements).forEach(([_, element]) => replaceUndefinedAttributes(element));
  setInterval(() => ack(), 3000);
  return (app = Vue.createApp({
    data() {
      return {
        elements,
      };
    },
    render() {
      return renderRecursively(this.elements, 0);
    },
    mounted() {
      setMountedApp(this);
      window.documentId = createRandomUUID();
      window.clientId = options.query.client_id;
      const url = window.location.protocol === "https:" ? "wss://" : "ws://" + window.location.host;
      window.path_prefix = options.prefix;
      window.nextMessageId = options.query.next_message_id;
      window.ackedMessageId = -1;
      window.socket = io(url, {
        path: `${options.prefix}/_nicegui_ws/socket.io`,
        query: options.query,
        extraHeaders: options.extraHeaders,
        transports:
          "prerendering" in document && document.prerendering === true
            ? ["polling", ...options.transports]
            : options.transports,
      });
      window.did_handshake = false;
      const messageHandlers = {
        connect: () => {
          function wrapFunction(originalFunction) {
            const MAX_WEBSOCKET_MESSAGE_SIZE = 1000000 - 100; // 1MB without 100 bytes of slack for the message header
            return function (...args) {
              const msg = args[0];
              if (typeof msg === "string" && msg.length > MAX_WEBSOCKET_MESSAGE_SIZE) {
                const errorMessage = `Payload size ${msg.length} exceeds the maximum allowed limit.`;
                console.error(errorMessage);
                args[0] = `42["log",{"client_id":"${window.clientId}","level":"error","message":"${errorMessage}"}]`;
                if (window.tooLongMessageTimerId) clearTimeout(window.tooLongMessageTimerId);
                const popup = document.getElementById("too_long_message_popup");
                popup.ariaHidden = false;
                window.tooLongMessageTimerId = setTimeout(() => (popup.ariaHidden = true), 5000);
              }
              return originalFunction.call(this, ...args);
            };
          }
          const transport = window.socket.io.engine.transport;
          if (transport?.ws?.send) transport.ws.send = wrapFunction(transport.ws.send);
          if (transport?.doWrite) transport.doWrite = wrapFunction(transport.doWrite);

          const args = {
            client_id: window.clientId,
            document_id: window.documentId,
            tab_id: TAB_ID,
            old_tab_id: OLD_TAB_ID,
            next_message_id: window.nextMessageId,
          };
          window.socket.emit("handshake", args, (ok) => {
            if (!ok) {
              console.log("reloading because handshake failed for clientId " + window.clientId);
              window.location.reload();
            }
            window.did_handshake = true;
            document.getElementById("popup").ariaHidden = true;
          });
        },
        connect_error: (err) => {
          if (err.message == "timeout") {
            console.log("reloading because connection timed out");
            window.location.reload(); // see https://github.com/zauberzeug/nicegui/issues/198
          }
        },
        try_reconnect: async () => {
          document.getElementById("popup").ariaHidden = false;
          await fetch(window.location.href, { headers: { "NiceGUI-Check": "try_reconnect" } });
          console.log("reloading because reconnect was requested");
          window.location.reload();
        },
        disconnect: () => {
          document.getElementById("popup").ariaHidden = false;
        },
        load_js_components: async (msg) => {
          const urls = msg.components.map((c) => `${options.prefix}/_nicegui/${options.version}/components/${c.key}`);
          const imports = await Promise.all(urls.map((url) => import(url)));
          msg.components.forEach((c, i) => app.component(c.tag, imports[i].default));
        },
        update: async (msg) => {
          let eventListenersChanged = false;
          for (const [id, element] of Object.entries(msg)) {
            if (element === null) continue;
            if (!(id in this.elements)) continue;
            const oldListenerIds = new Set((this.elements[id]?.events || []).map((ev) => ev.listener_id));
            if (element.events?.some((e) => !oldListenerIds.has(e.listener_id))) {
              delete this.elements[id];
              eventListenersChanged = true;
            }
          }
          if (eventListenersChanged) {
            logAndEmit("warning", "Event listeners changed after initial definition. Re-rendering affected elements.");
            await this.$nextTick();
          }

          for (const [id, element] of Object.entries(msg)) {
            if (element === null) {
              delete this.elements[id];
              continue;
            }
            replaceUndefinedAttributes(element);
            this.elements[id] = element;
          }

          await this.$nextTick();
          for (const [id, element] of Object.entries(msg)) {
            if (element?.update_method) {
              getElement(id)?.[element.update_method]();
            }
          }
        },
        run_javascript: (msg) => runJavascript(msg.code, msg.request_id),
        open: (msg) => {
          const url = msg.path.startsWith("/") ? options.prefix + msg.path : msg.path;
          const target = msg.new_tab ? "_blank" : "_self";
          window.open(url, target);
        },
        download: (msg) => download(msg.src, msg.filename, msg.media_type, options.prefix),
        notify: (msg) => Quasar.Notify.create(msg),
      };
      const socketMessageQueue = [];
      let isProcessingSocketMessage = false;
      for (const [event, handler] of Object.entries(messageHandlers)) {
        window.socket.on(event, async (...args) => {
          if (args.length > 0 && args[0]._id !== undefined) {
            const message_id = args[0]._id;
            if (message_id < window.nextMessageId) return;
            window.nextMessageId = message_id + 1;
            delete args[0]._id;
          }
          socketMessageQueue.push(() => handler(...args));
          if (!isProcessingSocketMessage) {
            while (socketMessageQueue.length > 0) {
              const handler = socketMessageQueue.shift();
              isProcessingSocketMessage = true;
              try {
                await handler();
              } catch (e) {
                console.error(e);
              }
              isProcessingSocketMessage = false;
            }
          }
        });
      }
    },
  }));
}
