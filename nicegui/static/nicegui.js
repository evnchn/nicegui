/* NiceGUI Client Bundle - Built with esbuild */
var NiceGUI = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __name = (target2, value2) => __defProp(target2, "name", { value: value2, configurable: true });
  var __export = (target2, all) => {
    for (var name in all)
      __defProp(target2, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key2 of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key2) && key2 !== except)
          __defProp(to, key2, { get: () => from[key2], enumerable: !(desc = __getOwnPropDesc(from, key2)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.js
  var index_exports = {};
  __export(index_exports, {
    False: () => False,
    None: () => None,
    OLD_TAB_ID: () => OLD_TAB_ID,
    TAB_ID: () => TAB_ID,
    True: () => True,
    ack: () => ack,
    applyColors: () => applyColors,
    createApp: () => createApp,
    download: () => download,
    emitEvent: () => emitEvent,
    getApp: () => getApp,
    getComputedProp: () => getComputedProp,
    getElement: () => getElement,
    getHtmlElement: () => getHtmlElement,
    getMountedApp: () => getMountedApp,
    logAndEmit: () => logAndEmit,
    parseElements: () => parseElements,
    replaceUndefinedAttributes: () => replaceUndefinedAttributes,
    runJavascript: () => runJavascript,
    runMethod: () => runMethod
  });

  // src/constants.js
  var True = true;
  var False = false;
  var None = void 0;

  // src/colors.js
  function applyColors(colors) {
    const quasarColors = ["primary", "secondary", "accent", "dark", "dark-page", "positive", "negative", "info", "warning"];
    let customCSS = "";
    for (let color in colors) {
      if (quasarColors.includes(color))
        continue;
      const colorName = color.replaceAll("_", "-");
      const colorVar = "--q-" + colorName;
      document.body.style.setProperty(colorVar, colors[color]);
      customCSS += `.text-${colorName} { color: var(${colorVar}) !important; }
`;
      customCSS += `.bg-${colorName} { background-color: var(${colorVar}) !important; }
`;
    }
    if (!customCSS) return;
    const style = document.createElement("style");
    style.innerHTML = customCSS;
    style.dataset.niceguiCustomColors = "";
    document.head.querySelectorAll("[data-nicegui-custom-colors]").forEach((el) => el.remove());
    document.getElementsByTagName("head")[0].appendChild(style);
  }
  __name(applyColors, "applyColors");

  // src/elements.js
  var mounted_app = void 0;
  function setMountedApp(app3) {
    mounted_app = app3;
  }
  __name(setMountedApp, "setMountedApp");
  function getMountedApp() {
    return mounted_app;
  }
  __name(getMountedApp, "getMountedApp");
  function replaceUndefinedAttributes(element2) {
    element2.class ??= [];
    element2.style ??= {};
    element2.props ??= {};
    element2.text ??= null;
    element2.events ??= [];
    element2.update_method ??= null;
    element2.slots = {
      default: { ids: element2.children || [] },
      ...element2.slots ?? {}
    };
  }
  __name(replaceUndefinedAttributes, "replaceUndefinedAttributes");
  function getElement(id2) {
    const _id = id2 instanceof Element ? id2.id.slice(1) : id2;
    return mounted_app.$refs["r" + _id];
  }
  __name(getElement, "getElement");
  function getHtmlElement(id2) {
    let id_as_a_string = id2.toString();
    if (!id_as_a_string.startsWith("c")) {
      id_as_a_string = "c" + id_as_a_string;
    }
    return document.getElementById(id_as_a_string);
  }
  __name(getHtmlElement, "getHtmlElement");

  // src/utils.js
  function parseElements(raw_elements) {
    return JSON.parse(
      raw_elements.replace(/&#36;/g, "$").replace(/&#96;/g, "`").replace(/&gt;/g, ">").replace(/&lt;/g, "<").replace(/&amp;/g, "&")
    );
  }
  __name(parseElements, "parseElements");
  function runMethod(target, method_name, args) {
    if (typeof target === "object") {
      if (method_name in target) {
        return target[method_name](...args);
      } else {
        return eval(method_name)(target, ...args);
      }
    }
    const element = getElement(target);
    if (element === null || element === void 0) return;
    if (method_name in element) {
      return element[method_name](...args);
    } else if (method_name in (element.$refs.qRef || [])) {
      return element.$refs.qRef[method_name](...args);
    } else {
      return eval(method_name)(element, ...args);
    }
  }
  __name(runMethod, "runMethod");
  function getComputedProp(target2, prop_name) {
    if (typeof target2 === "object" && prop_name in target2) {
      return target2[prop_name];
    }
    const element2 = getElement(target2);
    if (element2 === null || element2 === void 0) return;
    if (prop_name in element2) {
      return element2[prop_name];
    } else if (prop_name in (element2.$refs.qRef || [])) {
      return element2.$refs.qRef[prop_name];
    }
  }
  __name(getComputedProp, "getComputedProp");
  function emitEvent(event_name2, ...args2) {
    getElement(0).$emit(event_name2, ...args2);
  }
  __name(emitEvent, "emitEvent");
  function logAndEmit(level, message) {
    if (level === "error") {
      console.error(message);
    } else if (level === "warning") {
      console.warn(message);
    } else {
      console.log(message);
    }
    window.socket.emit("log", { client_id: window.clientId, level, message });
  }
  __name(logAndEmit, "logAndEmit");
  function runJavascript(code, request_id) {
    new Promise((resolve) => resolve(eval(code))).catch((reason) => {
      if (reason instanceof SyntaxError) return eval(`(async() => {${code}})()`);
      else throw reason;
    }).then((result) => {
      if (request_id) {
        window.socket.emit("javascript_response", { request_id, client_id: window.clientId, result });
      }
    });
  }
  __name(runJavascript, "runJavascript");
  function download(src, filename, mediaType, prefix) {
    const anchor = document.createElement("a");
    if (typeof src === "string") {
      anchor.href = src.startsWith("/") ? prefix + src : src;
    } else {
      anchor.href = URL.createObjectURL(new Blob([src], { type: mediaType }));
    }
    anchor.target = "_blank";
    anchor.download = filename || "";
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    if (typeof src !== "string") {
      URL.revokeObjectURL(anchor.href);
    }
  }
  __name(download, "download");
  function ack() {
    if (!window.socket || !window.did_handshake) return;
    if (window.ackedMessageId >= window.nextMessageId) return;
    window.socket.emit("ack", {
      client_id: window.clientId,
      next_message_id: window.nextMessageId
    });
    window.ackedMessageId = window.nextMessageId;
  }
  __name(ack, "ack");
  function createRandomUUID() {
    try {
      return crypto.randomUUID();
    } catch (e2) {
      return "10000000-1000-4000-8000-100000000000".replace(
        /[018]/g,
        (c) => (+c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> +c / 4).toString(16)
      );
    }
  }
  __name(createRandomUUID, "createRandomUUID");
  var OLD_TAB_ID = sessionStorage.__nicegui_tab_closed === "false" ? sessionStorage.__nicegui_tab_id : null;
  var TAB_ID = !sessionStorage.__nicegui_tab_id || sessionStorage.__nicegui_tab_closed === "false" ? sessionStorage.__nicegui_tab_id = createRandomUUID() : sessionStorage.__nicegui_tab_id;
  sessionStorage.__nicegui_tab_closed = "false";
  window.onbeforeunload = function() {
    sessionStorage.__nicegui_tab_closed = "true";
  };

  // src/events.js
  function stringifyEventArgs(args2, event_args) {
    const result = [];
    args2.forEach((arg, i) => {
      if (event_args !== null && i >= event_args.length) return;
      let filtered = {};
      if (typeof arg !== "object" || arg === null || Array.isArray(arg)) {
        filtered = arg;
      } else {
        for (let k in arg) {
          if (k == "originalTarget") {
            try {
              arg[k].toString();
            } catch (e2) {
              continue;
            }
          }
          if (event_args === null || event_args[i] === null || event_args[i].includes(k)) {
            filtered[k] = arg[k];
          }
        }
      }
      result.push(JSON.stringify(filtered, (k, v) => v instanceof Node || v instanceof Window ? void 0 : v));
    });
    return result;
  }
  __name(stringifyEventArgs, "stringifyEventArgs");
  var waitingCallbacks = /* @__PURE__ */ new Map();
  function throttle(callback, time, leading, trailing, id2) {
    if (time <= 0) {
      callback();
      return;
    }
    if (waitingCallbacks.has(id2)) {
      if (trailing) {
        waitingCallbacks.set(id2, callback);
      }
    } else {
      if (leading) {
        callback();
        waitingCallbacks.set(id2, null);
      } else if (trailing) {
        waitingCallbacks.set(id2, callback);
      }
      if (leading || trailing) {
        setTimeout(() => {
          const trailingCallback = waitingCallbacks.get(id2);
          if (trailingCallback) trailingCallback();
          waitingCallbacks.delete(id2);
        }, 1e3 * time);
      }
    }
  }
  __name(throttle, "throttle");

  // src/render.js
  function renderRecursively(elements, id, propsContext) {
    const element = elements[id];
    if (element === void 0) {
      return;
    }
    const props = {
      id: "c" + id,
      ref: "r" + id,
      key: id,
      // HACK: workaround for #600 and #898
      class: element.class.join(" ") || void 0,
      style: Object.entries(element.style).reduce((str, [p, val]) => `${str}${p}:${val};`, "") || void 0,
      ...element.props
    };
    Object.entries(props).forEach(([key, value]) => {
      if (key.startsWith(":")) {
        try {
          try {
            props[key.substring(1)] = new Function("props", `return (${value})`)(propsContext);
          } catch (e) {
            props[key.substring(1)] = eval(value);
          }
          delete props[key];
        } catch (e2) {
          console.error(`Error while converting ${key} attribute to function:`, e2);
        }
      }
    });
    element.events.forEach((event) => {
      let event_name = "on" + event.type[0].toLocaleUpperCase() + event.type.substring(1);
      event.specials.forEach((s) => event_name += s[0].toLocaleUpperCase() + s.substring(1));
      const emit = /* @__PURE__ */ __name((...args2) => {
        const emitter = /* @__PURE__ */ __name(() => window.socket?.emit("event", {
          id,
          client_id: window.clientId,
          listener_id: event.listener_id,
          args: stringifyEventArgs(args2, event.args)
        }), "emitter");
        const delayed_emitter = /* @__PURE__ */ __name(() => {
          if (window.did_handshake) emitter();
          else setTimeout(delayed_emitter, 10);
        }, "delayed_emitter");
        throttle(delayed_emitter, event.throttle, event.leading_events, event.trailing_events, event.listener_id);
        if (element.props["loopback"] === False && event.type == "update:modelValue") {
          element.props["model-value"] = args2;
        }
      }, "emit");
      let handler;
      if (event.js_handler) {
        const props = propsContext;
        handler = eval(event.js_handler);
      } else {
        handler = emit;
      }
      handler = Vue.withModifiers(handler, event.modifiers);
      handler = event.keys.length ? Vue.withKeys(handler, event.keys) : handler;
      if (props[event_name]) {
        props[event_name].push(handler);
      } else {
        props[event_name] = [handler];
      }
    });
    const slots = {};
    const element_slots = {
      default: { ids: element.children || [] },
      ...element.slots
    };
    Object.entries(element_slots).forEach(([name, data]) => {
      slots[name] = (props2) => {
        const rendered = [];
        if (data.template) {
          rendered.push(
            Vue.h(
              {
                props: { props: { type: Object, default: {} } },
                template: data.template
              },
              {
                props: props2
              }
            )
          );
        }
        const children = data.ids.map((id2) => renderRecursively(elements, id2, props2 || propsContext));
        if (name === "default" && element.text !== null) {
          children.unshift(element.text);
        }
        return [...rendered, ...children];
      };
    });
    const app = getApp();
    return Vue.h(app.config.isNativeTag(element.tag) ? element.tag : Vue.resolveComponent(element.tag), props, slots);
  }
  __name(renderRecursively, "renderRecursively");

  // src/app.js
  var app2 = void 0;
  function getApp() {
    return app2;
  }
  __name(getApp, "getApp");
  function createApp(elements2, options) {
    Object.entries(elements2).forEach(([_, element2]) => replaceUndefinedAttributes(element2));
    setInterval(() => ack(), 3e3);
    return app2 = Vue.createApp({
      data() {
        return {
          elements: elements2
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
          transports: "prerendering" in document && document.prerendering === true ? ["polling", ...options.transports] : options.transports
        });
        window.did_handshake = false;
        const messageHandlers = {
          connect: /* @__PURE__ */ __name(() => {
            function wrapFunction(originalFunction) {
              const MAX_WEBSOCKET_MESSAGE_SIZE = 1e6 - 100;
              return function(...args3) {
                const msg = args3[0];
                if (typeof msg === "string" && msg.length > MAX_WEBSOCKET_MESSAGE_SIZE) {
                  const errorMessage = `Payload size ${msg.length} exceeds the maximum allowed limit.`;
                  console.error(errorMessage);
                  args3[0] = `42["log",{"client_id":"${window.clientId}","level":"error","message":"${errorMessage}"}]`;
                  if (window.tooLongMessageTimerId) clearTimeout(window.tooLongMessageTimerId);
                  const popup = document.getElementById("too_long_message_popup");
                  popup.ariaHidden = false;
                  window.tooLongMessageTimerId = setTimeout(() => popup.ariaHidden = true, 5e3);
                }
                return originalFunction.call(this, ...args3);
              };
            }
            __name(wrapFunction, "wrapFunction");
            const transport = window.socket.io.engine.transport;
            if (transport?.ws?.send) transport.ws.send = wrapFunction(transport.ws.send);
            if (transport?.doWrite) transport.doWrite = wrapFunction(transport.doWrite);
            const args2 = {
              client_id: window.clientId,
              document_id: window.documentId,
              tab_id: TAB_ID,
              old_tab_id: OLD_TAB_ID,
              next_message_id: window.nextMessageId
            };
            window.socket.emit("handshake", args2, (ok) => {
              if (!ok) {
                console.log("reloading because handshake failed for clientId " + window.clientId);
                window.location.reload();
              }
              window.did_handshake = true;
              document.getElementById("popup").ariaHidden = true;
            });
          }, "connect"),
          connect_error: /* @__PURE__ */ __name((err) => {
            if (err.message == "timeout") {
              console.log("reloading because connection timed out");
              window.location.reload();
            }
          }, "connect_error"),
          try_reconnect: /* @__PURE__ */ __name(async () => {
            document.getElementById("popup").ariaHidden = false;
            await fetch(window.location.href, { headers: { "NiceGUI-Check": "try_reconnect" } });
            console.log("reloading because reconnect was requested");
            window.location.reload();
          }, "try_reconnect"),
          disconnect: /* @__PURE__ */ __name(() => {
            document.getElementById("popup").ariaHidden = false;
          }, "disconnect"),
          load_js_components: /* @__PURE__ */ __name(async (msg) => {
            const urls = msg.components.map((c) => `${options.prefix}/_nicegui/${options.version}/components/${c.key}`);
            const imports = await Promise.all(urls.map((url2) => import(url2)));
            msg.components.forEach((c, i) => app2.component(c.tag, imports[i].default));
          }, "load_js_components"),
          update: /* @__PURE__ */ __name(async (msg) => {
            let eventListenersChanged = false;
            for (const [id2, element2] of Object.entries(msg)) {
              if (element2 === null) continue;
              if (!(id2 in this.elements)) continue;
              const oldListenerIds = new Set((this.elements[id2]?.events || []).map((ev) => ev.listener_id));
              if (element2.events?.some((e2) => !oldListenerIds.has(e2.listener_id))) {
                delete this.elements[id2];
                eventListenersChanged = true;
              }
            }
            if (eventListenersChanged) {
              logAndEmit("warning", "Event listeners changed after initial definition. Re-rendering affected elements.");
              await this.$nextTick();
            }
            for (const [id2, element2] of Object.entries(msg)) {
              if (element2 === null) {
                delete this.elements[id2];
                continue;
              }
              replaceUndefinedAttributes(element2);
              this.elements[id2] = element2;
            }
            await this.$nextTick();
            for (const [id2, element2] of Object.entries(msg)) {
              if (element2?.update_method) {
                getElement(id2)?.[element2.update_method]();
              }
            }
          }, "update"),
          run_javascript: /* @__PURE__ */ __name((msg) => runJavascript(msg.code, msg.request_id), "run_javascript"),
          open: /* @__PURE__ */ __name((msg) => {
            const url2 = msg.path.startsWith("/") ? options.prefix + msg.path : msg.path;
            const target2 = msg.new_tab ? "_blank" : "_self";
            window.open(url2, target2);
          }, "open"),
          download: /* @__PURE__ */ __name((msg) => download(msg.src, msg.filename, msg.media_type, options.prefix), "download"),
          notify: /* @__PURE__ */ __name((msg) => Quasar.Notify.create(msg), "notify")
        };
        const socketMessageQueue = [];
        let isProcessingSocketMessage = false;
        for (const [event2, handler2] of Object.entries(messageHandlers)) {
          window.socket.on(event2, async (...args2) => {
            if (args2.length > 0 && args2[0]._id !== void 0) {
              const message_id = args2[0]._id;
              if (message_id < window.nextMessageId) return;
              window.nextMessageId = message_id + 1;
              delete args2[0]._id;
            }
            socketMessageQueue.push(() => handler2(...args2));
            if (!isProcessingSocketMessage) {
              while (socketMessageQueue.length > 0) {
                const handler3 = socketMessageQueue.shift();
                isProcessingSocketMessage = true;
                try {
                  await handler3();
                } catch (e2) {
                  console.error(e2);
                }
                isProcessingSocketMessage = false;
              }
            }
          });
        }
      }
    });
  }
  __name(createApp, "createApp");

  // src/quasar-hack.js
  for (const importRule of document.styleSheets[0].cssRules) {
    if (importRule instanceof CSSImportRule && /quasar/.test(importRule.styleSheet?.href)) {
      for (const rule of Array.from(importRule.styleSheet.cssRules)) {
        if (rule instanceof CSSStyleRule && /\.q-card > div/.test(rule.selectorText)) {
          if (/\.q-card > div/.test(rule.selectorText)) rule.selectorText = ".nicegui-card-tight" + rule.selectorText;
        }
      }
    }
  }
  return __toCommonJS(index_exports);
})();

// Flatten exports to window for backwards compatibility
if (typeof window !== "undefined") {
  const exports = NiceGUI;
  window.True = exports.True;
  window.False = exports.False;
  window.None = exports.None;
  window.getElement = exports.getElement;
  window.getHtmlElement = exports.getHtmlElement;
  window.runMethod = exports.runMethod;
  window.getComputedProp = exports.getComputedProp;
  window.emitEvent = exports.emitEvent;
  window.logAndEmit = exports.logAndEmit;
  window.runJavascript = exports.runJavascript;
  window.download = exports.download;
  window.ack = exports.ack;
  window.parseElements = exports.parseElements;
  window.createApp = exports.createApp;
  window.applyColors = exports.applyColors;
  window.TAB_ID = exports.TAB_ID;
  window.OLD_TAB_ID = exports.OLD_TAB_ID;

  // Expose app and mounted_app via getters
  Object.defineProperty(window, "mounted_app", {
    get: exports.getMountedApp,
    enumerable: true,
    configurable: true
  });

  Object.defineProperty(window, "app", {
    get: exports.getApp,
    enumerable: true,
    configurable: true
  });
}

