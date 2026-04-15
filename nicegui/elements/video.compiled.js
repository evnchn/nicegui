// AUTO-GENERATED from video.js — DO NOT EDIT
import { openBlock as _openBlock, createElementBlock as _createElementBlock } from "vue"

const _hoisted_1 = ["controls", "autoplay", "muted", "src"]

export default {
  render(_ctx, _cache) {
  return (_openBlock(), _createElementBlock("video", {
    controls: _ctx.controls,
    autoplay: _ctx.autoplay,
    muted: _ctx.muted,
    src: _ctx.computed_src
  }, null, 8 /* PROPS */, _hoisted_1))
},
  props: {
    controls: Boolean,
    autoplay: Boolean,
    muted: Boolean,
    src: String,
  },
  data: function () {
    return {
      computed_src: undefined,
    };
  },
  mounted() {
    setTimeout(() => this.compute_src(), 0); // NOTE: wait for window.path_prefix to be set in app.mounted()
  },
  updated() {
    this.compute_src();
  },
  methods: {
    compute_src() {
      this.computed_src = (this.src.startsWith("/") ? window.path_prefix : "") + this.src;
    },
    seek(seconds) {
      this.$el.currentTime = seconds;
    },
    play() {
      this.$el.play();
    },
    pause() {
      this.$el.pause();
    },
  },
};
