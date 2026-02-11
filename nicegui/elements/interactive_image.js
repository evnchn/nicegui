import { toHandlers as _toHandlers, mergeProps as _mergeProps, createElementVNode as _createElementVNode, openBlock as _openBlock, createElementBlock as _createElementBlock, createCommentVNode as _createCommentVNode, renderSlot as _renderSlot, normalizeStyle as _normalizeStyle } from "vue"

const _hoisted_1 = ["src"]
const _hoisted_2 = ["viewBox"]
const _hoisted_3 = ["x1", "x2", "stroke"]
const _hoisted_4 = ["y1", "y2", "stroke"]
const _hoisted_5 = { ref: "contentGroup" }

export default {
  render(_ctx, _cache) {
  return (_openBlock(), _createElementBlock("div", {
    style: _normalizeStyle({ position: 'relative', aspectRatio: _ctx.size ? _ctx.size[0] / _ctx.size[1] : undefined })
  }, [
    _createElementVNode("img", _mergeProps({
      ref: "img",
      src: _ctx.computed_src,
      style: { width: '100%', height: '100%', opacity: _ctx.src ? 1 : 0 },
      onLoad: _cache[0] || (_cache[0] = (...args) => (_ctx.onImageLoaded && _ctx.onImageLoaded(...args)))
    }, _toHandlers({..._ctx.onCrossEvents, ..._ctx.onUserEvents}, true), { draggable: "false" }), null, 16 /* FULL_PROPS */, _hoisted_1),
    (_openBlock(), _createElementBlock("svg", {
      ref: "svg",
      style: {"position":"absolute","top":"0","left":"0","width":"100%","height":"100%","pointer-events":"none"},
      viewBox: _ctx.viewBox,
      preserveAspectRatio: "none"
    }, [
      _createElementVNode("g", {
        style: _normalizeStyle({ display: _ctx.showCross ? 'block' : 'none' })
      }, [
        (_ctx.cross)
          ? (_openBlock(), _createElementBlock("line", {
              key: 0,
              x1: _ctx.x,
              y1: "0",
              x2: _ctx.x,
              y2: "100%",
              stroke: _ctx.cross === true ? 'black' : _ctx.cross
            }, null, 8 /* PROPS */, _hoisted_3))
          : _createCommentVNode("v-if", true),
        (_ctx.cross)
          ? (_openBlock(), _createElementBlock("line", {
              key: 1,
              x1: "0",
              y1: _ctx.y,
              x2: "100%",
              y2: _ctx.y,
              stroke: _ctx.cross === true ? 'black' : _ctx.cross
            }, null, 8 /* PROPS */, _hoisted_4))
          : _createCommentVNode("v-if", true),
        _renderSlot(_ctx.$slots, "cross", {
          x: _ctx.x,
          y: _ctx.y
        })
      ], 4 /* STYLE */),
      _createElementVNode("g", _hoisted_5, null, 512 /* NEED_PATCH */)
    ], 8 /* PROPS */, _hoisted_2)),
    _renderSlot(_ctx.$slots, "default")
  ], 4 /* STYLE */))
},
  data() {
    return {
      viewBox: "0 0 0 0",
      loaded_image_width: 0,
      loaded_image_height: 0,
      x: 100,
      y: 100,
      showCross: false,
      computed_src: undefined,
      waiting_source: undefined,
      loading: false,
      DOMPurify: null,
    };
  },
  mounted() {
    if (this.sanitize) {
      import("dompurify").then(({ default: DOMPurify }) => {
        this.DOMPurify = DOMPurify;
        this.renderContent();
      });
    } else {
      this.renderContent();
    }
    setTimeout(() => this.compute_src(), 0); // NOTE: wait for window.path_prefix to be set in app.mounted()
    const handle_completion = () => {
      if (this.waiting_source) {
        this.computed_src = this.waiting_source;
        this.waiting_source = undefined;
      } else {
        this.loading = false;
      }
    };
    this.$refs.img.addEventListener("load", handle_completion);
    this.$refs.img.addEventListener("error", handle_completion);
    for (const event of [
      "pointermove",
      "pointerdown",
      "pointerup",
      "pointerover",
      "pointerout",
      "pointerenter",
      "pointerleave",
      "pointercancel",
    ]) {
      this.$refs.svg.addEventListener(event, (e) => this.onPointerEvent(event, e));
    }
  },
  updated() {
    this.renderContent();
    this.compute_src();
  },
  methods: {
    renderContent() {
      const content = this.content || "";
      if (this.sanitize) {
        if (!this.DOMPurify) return;
        const sanitized = this.DOMPurify.sanitize(`<svg>${content}</svg>`, {
          USE_PROFILES: { svg: true, svgFilters: true },
        });
        const match = sanitized.match(/^<svg>(.*)<\/svg>$/is);
        this.$refs.contentGroup.innerHTML = match ? match[1] : "";
      } else {
        this.$refs.contentGroup.innerHTML = content;
      }
    },
    compute_src() {
      const suffix = this.t ? (this.src.includes("?") ? "&" : "?") + "_nicegui_t=" + this.t : "";
      const new_src = (this.src.startsWith("/") ? window.path_prefix : "") + this.src + suffix;
      if (new_src == this.computed_src) {
        return;
      }
      if (this.loading) {
        this.waiting_source = new_src;
      } else {
        this.computed_src = new_src;
        this.loading = true;
      }
      if (!this.src && this.size) {
        this.updateViewbox(this.size[0], this.size[1]);
      }
    },
    updateCrossHair(e) {
      const width = this.src ? this.loaded_image_width : this.size ? this.size[0] : 1;
      const height = this.src ? this.loaded_image_height : this.size ? this.size[1] : 1;
      this.x = (e.offsetX * width) / e.target.clientWidth;
      this.y = (e.offsetY * height) / e.target.clientHeight;
    },
    onImageLoaded(e) {
      this.loaded_image_width = e.target.naturalWidth;
      this.loaded_image_height = e.target.naturalHeight;
      this.updateViewbox(this.loaded_image_width, this.loaded_image_height);
      this.$emit("loaded", { width: this.loaded_image_width, height: this.loaded_image_height, source: e.target.src });
    },
    onMouseEvent(type, e) {
      const imageWidth = this.src ? this.loaded_image_width : this.size ? this.size[0] : 1;
      const imageHeight = this.src ? this.loaded_image_height : this.size ? this.size[1] : 1;
      this.$emit("mouse", {
        mouse_event_type: type,
        image_x: (e.offsetX * imageWidth) / this.$refs.img.clientWidth,
        image_y: (e.offsetY * imageHeight) / this.$refs.img.clientHeight,
        button: e.button,
        buttons: e.buttons,
        altKey: e.altKey,
        ctrlKey: e.ctrlKey,
        metaKey: e.metaKey,
        shiftKey: e.shiftKey,
      });
    },
    onPointerEvent(type, e) {
      const imageWidth = this.src ? this.loaded_image_width : this.size ? this.size[0] : 1;
      const imageHeight = this.src ? this.loaded_image_height : this.size ? this.size[1] : 1;
      this.$emit(`svg:${type}`, {
        type: type,
        element_id: e.target.id,
        image_x: (e.offsetX * imageWidth) / this.$refs.svg.clientWidth,
        image_y: (e.offsetY * imageHeight) / this.$refs.svg.clientHeight,
      });
    },
    updateViewbox(width, height) {
      this.viewBox = `0 0 ${width} ${height}`;
    },
  },
  computed: {
    onCrossEvents() {
      if (!this.cross && !this.$slots.cross) return {};
      return {
        mouseenter: () => (this.showCross = true),
        mouseleave: () => (this.showCross = false),
        mousemove: (event) => this.updateCrossHair(event),
      };
    },
    onUserEvents() {
      const events = {};
      for (const type of this.events || []) {
        events[type] = (event) => this.onMouseEvent(type, event);
      }
      return events;
    },
  },
  props: {
    src: String,
    content: String,
    size: Object,
    events: Array,
    cross: Boolean,
    t: String,
    sanitize: Boolean,
  },
};
