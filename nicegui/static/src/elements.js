import { None } from "./constants.js";

let mounted_app = undefined;

export function setMountedApp(app) {
  mounted_app = app;
}

export function getMountedApp() {
  return mounted_app;
}

export function replaceUndefinedAttributes(element) {
  element.class ??= [];
  element.style ??= {};
  element.props ??= {};
  element.text ??= null;
  element.events ??= [];
  element.update_method ??= null;
  element.slots = {
    default: { ids: element.children || [] },
    ...(element.slots ?? {}),
  };
}

export function getElement(id) {
  const _id = id instanceof Element ? id.id.slice(1) : id;
  return mounted_app.$refs["r" + _id];
}

export function getHtmlElement(id) {
  let id_as_a_string = id.toString();
  if (!id_as_a_string.startsWith("c")) {
    id_as_a_string = "c" + id_as_a_string;
  }
  return document.getElementById(id_as_a_string);
}
