import { getElement } from "./elements.js";

export function parseElements(raw_elements) {
  return JSON.parse(
    raw_elements
      .replace(/&#36;/g, "$")
      .replace(/&#96;/g, "`")
      .replace(/&gt;/g, ">")
      .replace(/&lt;/g, "<")
      .replace(/&amp;/g, "&")
  );
}

export function runMethod(target, method_name, args) {
  if (typeof target === "object") {
    if (method_name in target) {
      return target[method_name](...args);
    } else {
      return eval(method_name)(target, ...args);
    }
  }
  const element = getElement(target);
  if (element === null || element === undefined) return;
  if (method_name in element) {
    return element[method_name](...args);
  } else if (method_name in (element.$refs.qRef || [])) {
    return element.$refs.qRef[method_name](...args);
  } else {
    return eval(method_name)(element, ...args);
  }
}

export function getComputedProp(target, prop_name) {
  if (typeof target === "object" && prop_name in target) {
    return target[prop_name];
  }
  const element = getElement(target);
  if (element === null || element === undefined) return;
  if (prop_name in element) {
    return element[prop_name];
  } else if (prop_name in (element.$refs.qRef || [])) {
    return element.$refs.qRef[prop_name];
  }
}

export function emitEvent(event_name, ...args) {
  getElement(0).$emit(event_name, ...args);
}

export function logAndEmit(level, message) {
  if (level === "error") {
    console.error(message);
  } else if (level === "warning") {
    console.warn(message);
  } else {
    console.log(message);
  }
  window.socket.emit("log", { client_id: window.clientId, level, message });
}

export function runJavascript(code, request_id) {
  new Promise((resolve) => resolve(eval(code)))
    .catch((reason) => {
      if (reason instanceof SyntaxError) return eval(`(async() => {${code}})()`);
      else throw reason;
    })
    .then((result) => {
      if (request_id) {
        window.socket.emit("javascript_response", { request_id, client_id: window.clientId, result });
      }
    });
}

export function download(src, filename, mediaType, prefix) {
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

export function ack() {
  if (!window.socket || !window.did_handshake) return;
  if (window.ackedMessageId >= window.nextMessageId) return;
  window.socket.emit("ack", {
    client_id: window.clientId,
    next_message_id: window.nextMessageId,
  });
  window.ackedMessageId = window.nextMessageId;
}

export function createRandomUUID() {
  try {
    return crypto.randomUUID();
  } catch (e) {
    // https://stackoverflow.com/a/2117523/3419103
    return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
      (+c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (+c / 4)))).toString(16)
    );
  }
}

export const OLD_TAB_ID = sessionStorage.__nicegui_tab_closed === "false" ? sessionStorage.__nicegui_tab_id : null;
export const TAB_ID =
  !sessionStorage.__nicegui_tab_id || sessionStorage.__nicegui_tab_closed === "false"
    ? (sessionStorage.__nicegui_tab_id = createRandomUUID())
    : sessionStorage.__nicegui_tab_id;
sessionStorage.__nicegui_tab_closed = "false";
window.onbeforeunload = function () {
  sessionStorage.__nicegui_tab_closed = "true";
};
