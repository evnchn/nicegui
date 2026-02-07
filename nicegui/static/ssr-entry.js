import * as Vue from 'vue';
import { renderToString } from 'vue/server-renderer';

// Expose Vue globally so the Quasar UMD build (loaded separately) can find it.
globalThis.Vue = Vue;

globalThis.renderNiceGUIToString = async function(elementsJson) {
  const { createSSRApp, h, resolveComponent, createCommentVNode, renderSlot } = Vue;

  // Wrap slot functions with renderSlot to produce Fragment VNodes matching compiled templates.
  // Browser templates compile <slot></slot> to renderSlot() which wraps content in a Fragment.
  // Without this, SSR slot arrays lack Fragment markers and cause hydration node mismatches.
  function wrapSlots($slots) {
    const result = {};
    for (const name in $slots) {
      result[name] = (props) => [renderSlot($slots, name, props)];
    }
    return result;
  }
  const elements = JSON.parse(elementsJson);

  // Replace undefined-like values (same as nicegui.js replaceUndefinedAttributes)
  Object.values(elements).forEach(element => {
    element.class = element.class || [];
    element.style = element.style || {};
    element.props = element.props || {};
    element.text = element.text ?? null;
    element.events = element.events || [];
    element.slots = {
      default: { ids: element.children || [] },
      ...(element.slots || {}),
    };
  });

  // Mirror the client-side renderRecursively (nicegui.js) as closely as possible
  // to ensure SSR output matches the client's first render for clean hydration.
  function renderRecursively(elements, id) {
    const element = elements[id];
    if (element === undefined) return;

    // Build props exactly like nicegui.js does
    const props = {
      id: 'c' + id,
      ref: 'r' + id,
      key: id,
      class: element.class.join(' ') || undefined,
      style: Object.entries(element.style).reduce((str, [p, val]) => `${str}${p}:${val};`, '') || undefined,
      ...element.props,
    };

    // Evaluate ':'-prefixed dynamic bindings (same as nicegui.js)
    Object.entries(props).forEach(([key, value]) => {
      if (key.startsWith(':')) {
        try {
          props[key.substring(1)] = new Function('props', `return (${value})`)(undefined);
        } catch (e) {
          // Skip dynamic bindings that fail in SSR context
        }
        delete props[key];
      }
    });

    // Skip '@'-prefixed event bindings (no event handling in SSR)
    Object.keys(props).forEach(key => {
      if (key.startsWith('@')) delete props[key];
    });

    // Build slots (mirror nicegui.js slot structure)
    const element_slots = element.slots;
    const slots = {};
    Object.entries(element_slots).forEach(([name, data]) => {
      slots[name] = () => {
        const rendered = [];
        (data.ids || []).forEach(childId => {
          const child = renderRecursively(elements, childId);
          if (child) rendered.push(child);
        });
        return rendered;
      };
    });

    if (element.text !== null && element.text !== undefined) {
      const origDefault = slots.default;
      slots.default = () => {
        const children = origDefault ? origDefault() : [];
        children.unshift(String(element.text));
        return children;
      };
    }

    const tag = element.tag;
    const isNative = !tag.includes('-');
    const resolvedTag = isNative ? tag : resolveComponent(tag);
    if (isNative) {
      const children = slots.default ? slots.default() : undefined;
      return h(resolvedTag, props, children && children.length > 0 ? children : undefined);
    } else {
      return h(resolvedTag, props, Object.keys(slots).length > 0 ? slots : undefined);
    }
  }

  const app = createSSRApp({
    data() {
      return { elements };
    },
    render() {
      return renderRecursively(this.elements, 0);
    },
  });

  // Register Quasar from the UMD build (loaded via globalThis.Quasar)
  if (globalThis.Quasar) {
    app.use(globalThis.Quasar, { config: {} });
  }

  // --- NiceGUI Component SSR Wrappers ---
  // These mirror the client-side NiceGUI JS components so SSR output matches hydration.
  // Each wrapper consumes component-specific props and forwards $attrs to the root element.

  // Renderless component (no visual output, produces comment node <!---->)
  const renderless = { render() { return null; } };

  // Quasar wrappers
  app.component('nicegui-input', {
    inheritAttrs: false,
    props: { _autocomplete: Array, value: { default: '' }, id: String },
    render() {
      return [
        h(resolveComponent('q-input'), {
          ...this.$attrs,
          'model-value': this.value ?? '',
          list: this.id + '-datalist',
        }, wrapSlots(this.$slots)),
        createCommentVNode(''),
      ];
    },
  });

  app.component('nicegui-select', {
    inheritAttrs: false,
    props: { options: Array },
    render() {
      return h(resolveComponent('q-select'), { ...this.$attrs, options: this.options }, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-table', {
    inheritAttrs: false,
    props: { columns: Array },
    render() {
      return h(resolveComponent('q-table'), { ...this.$attrs, columns: this.columns }, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-dialog', {
    inheritAttrs: false,
    render() {
      return h(resolveComponent('q-dialog'), this.$attrs, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-expansion', {
    inheritAttrs: false,
    render() {
      const wrapped = wrapSlots(this.$slots);
      const slots = {};
      Object.entries(wrapped).forEach(([name, fn]) => {
        if (name !== 'default') slots[name] = fn;
      });
      slots.default = () => [
        h('div', { class: 'nicegui-expansion-content' },
          this.$slots.default ? [renderSlot(this.$slots, 'default')] : []),
      ];
      return h(resolveComponent('q-expansion-item'), this.$attrs, slots);
    },
  });

  app.component('nicegui-header', {
    inheritAttrs: false,
    props: { addScrollPadding: Boolean },
    render() {
      return h(resolveComponent('q-header'), this.$attrs, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-image', {
    inheritAttrs: false,
    props: { src: String, t: String },
    render() {
      return h(resolveComponent('q-img'), { ...this.$attrs, src: this.src }, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-upload', {
    inheritAttrs: false,
    props: { url: String },
    render() {
      return h(resolveComponent('q-uploader'), { ...this.$attrs, url: this.url }, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-editor', {
    inheritAttrs: false,
    props: { value: { default: '' }, id: String },
    render() {
      return h(resolveComponent('q-editor'), { ...this.$attrs, 'model-value': this.value ?? '', id: this.id }, wrapSlots(this.$slots));
    },
  });

  app.component('nicegui-log', {
    inheritAttrs: false,
    render() {
      return h(resolveComponent('q-scroll-area'), this.$attrs, wrapSlots(this.$slots));
    },
  });

  // Native element wrappers
  app.component('nicegui-link', {
    inheritAttrs: false,
    props: { href: String, target: String },
    render() {
      return h('a', { ...this.$attrs, href: this.href, target: this.target }, this.$slots);
    },
  });

  app.component('nicegui-audio', {
    inheritAttrs: false,
    props: { controls: Boolean, autoplay: Boolean, muted: Boolean, src: String },
    render() {
      return h('audio', { ...this.$attrs, controls: this.controls, autoplay: this.autoplay, muted: this.muted, src: this.src });
    },
  });

  app.component('nicegui-video', {
    inheritAttrs: false,
    props: { controls: Boolean, autoplay: Boolean, muted: Boolean, src: String },
    render() {
      return h('video', { ...this.$attrs, controls: this.controls, autoplay: this.autoplay, muted: this.muted, src: this.src });
    },
  });

  // Container wrappers
  app.component('nicegui-code', {
    inheritAttrs: false,
    props: { content: String },
    render() {
      return h('div', this.$attrs, this.$slots);
    },
  });

  app.component('nicegui-html', {
    inheritAttrs: false,
    props: { innerHTML: String, sanitize: Boolean, tag: { default: 'div' } },
    render() {
      return h(this.tag || 'div', this.$attrs);
    },
  });

  app.component('nicegui-markdown', {
    inheritAttrs: false,
    props: { innerHTML: String, dynamicResourcePath: String, resourceName: String, sanitize: Boolean, useMermaid: Boolean },
    render() {
      return h('div', this.$attrs);
    },
  });

  app.component('nicegui-sub-pages', {
    inheritAttrs: false,
    render() {
      return h('div', this.$attrs, this.$slots);
    },
  });

  app.component('nicegui-interactive-image', {
    inheritAttrs: false,
    props: { src: String, content: String, size: Object, events: Array, cross: Boolean, t: String, sanitize: Boolean },
    render() {
      return h('div', { ...this.$attrs, style: (this.$attrs.style || '') + ';position:relative' }, [
        h('img', { src: this.src, style: 'width:100%;height:auto' }),
      ]);
    },
  });

  app.component('nicegui-teleport', {
    inheritAttrs: false,
    props: { to: String },
    render() { return null; },
  });

  // Renderless components (side-effects only, no visual output)
  app.component('nicegui-colors', renderless);
  app.component('nicegui-dark-mode', renderless);
  app.component('nicegui-fullscreen', renderless);
  app.component('nicegui-keyboard', renderless);
  app.component('nicegui-notification', renderless);
  app.component('nicegui-query', renderless);
  app.component('nicegui-timer', renderless);

  // Suppress warnings for unregistered custom components (third-party, etc.)
  app.config.warnHandler = () => {};

  try {
    const html = await renderToString(app);
    return html;
  } catch (e) {
    return `<!-- SSR Error: ${e.message} -->`;
  }
};
