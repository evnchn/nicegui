// Import all modules
import { True, False, None } from "./constants.js";
import { applyColors } from "./colors.js";
import { getElement, getHtmlElement, replaceUndefinedAttributes, getMountedApp } from "./elements.js";
import { parseElements, runMethod, getComputedProp, emitEvent, logAndEmit, runJavascript, download, ack, TAB_ID, OLD_TAB_ID } from "./utils.js";
import { createApp, getApp } from "./app.js";
import "./quasar-hack.js";

// Export everything - window assignments handled by esbuild footer
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
