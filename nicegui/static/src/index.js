// Import all modules
import { True, False, None } from "./constants.js";
import { applyColors } from "./colors.js";
import { getElement, getHtmlElement, replaceUndefinedAttributes, getMountedApp } from "./elements.js";
import { parseElements, runMethod, getComputedProp, emitEvent, logAndEmit, runJavascript, download, ack, TAB_ID, OLD_TAB_ID } from "./utils.js";
import { createApp, getApp } from "./app.js";
import "./quasar-hack.js";

// Make all functions globally available for backwards compatibility
// Python code uses run_javascript to call these functions
if (typeof window !== "undefined") {
  window.True = True;
  window.False = False;
  window.None = None;
  window.getElement = getElement;
  window.getHtmlElement = getHtmlElement;
  window.runMethod = runMethod;
  window.getComputedProp = getComputedProp;
  window.emitEvent = emitEvent;
  window.logAndEmit = logAndEmit;
  window.runJavascript = runJavascript;
  window.download = download;
  window.ack = ack;
  window.parseElements = parseElements;
  window.createApp = createApp;
  window.applyColors = applyColors;
  window.TAB_ID = TAB_ID;
  window.OLD_TAB_ID = OLD_TAB_ID;

  // Expose mounted_app via getter for backwards compatibility
  Object.defineProperty(window, "mounted_app", {
    get: getMountedApp,
    enumerable: true,
    configurable: true
  });

  // Expose app via getter for backwards compatibility
  Object.defineProperty(window, "app", {
    get: getApp,
    enumerable: true,
    configurable: true
  });
}

// Re-export everything for potential ES module usage
export {
  True,
  False,
  None,
  applyColors,
  getElement,
  getHtmlElement,
  replaceUndefinedAttributes,
  parseElements,
  runMethod,
  getComputedProp,
  emitEvent,
  logAndEmit,
  runJavascript,
  download,
  ack,
  createApp,
  getApp,
  getMountedApp,
  TAB_ID,
  OLD_TAB_ID,
};
