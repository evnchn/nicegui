import { True, False, None } from "./constants.js";
import { stringifyEventArgs, throttle } from "./events.js";
import { getElement } from "./elements.js";
import { getApp } from "./app.js";

export function renderRecursively(elements, id, propsContext) {
  const element = elements[id];
  if (element === undefined) {
    return;
  }

  const props = {
    id: "c" + id,
    ref: "r" + id,
    key: id, // HACK: workaround for #600 and #898
    class: element.class.join(" ") || undefined,
    style: Object.entries(element.style).reduce((str, [p, val]) => `${str}${p}:${val};`, "") || undefined,
    ...element.props,
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
      } catch (e) {
        console.error(`Error while converting ${key} attribute to function:`, e);
      }
    }
  });
  element.events.forEach((event) => {
    let event_name = "on" + event.type[0].toLocaleUpperCase() + event.type.substring(1);
    event.specials.forEach((s) => (event_name += s[0].toLocaleUpperCase() + s.substring(1)));

    const emit = (...args) => {
      const emitter = () =>
        window.socket?.emit("event", {
          id: id,
          client_id: window.clientId,
          listener_id: event.listener_id,
          args: stringifyEventArgs(args, event.args),
        });
      const delayed_emitter = () => {
        if (window.did_handshake) emitter();
        else setTimeout(delayed_emitter, 10);
      };
      throttle(delayed_emitter, event.throttle, event.leading_events, event.trailing_events, event.listener_id);
      if (element.props["loopback"] === False && event.type == "update:modelValue") {
        element.props["model-value"] = args;
      }
    };

    let handler;
    if (event.js_handler) {
      const props = propsContext; // make `props` accessible from inside the event handler
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
    ...element.slots,
  };
  Object.entries(element_slots).forEach(([name, data]) => {
    slots[name] = (props) => {
      const rendered = [];
      if (data.template) {
        rendered.push(
          Vue.h(
            {
              props: { props: { type: Object, default: {} } },
              template: data.template,
            },
            {
              props: props,
            }
          )
        );
      }
      const children = data.ids.map((id) => renderRecursively(elements, id, props || propsContext));
      if (name === "default" && element.text !== null) {
        children.unshift(element.text);
      }
      return [...rendered, ...children];
    };
  });
  const app = getApp();
  return Vue.h(app.config.isNativeTag(element.tag) ? element.tag : Vue.resolveComponent(element.tag), props, slots);
}
