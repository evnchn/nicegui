// AUTO-GENERATED from log.js — DO NOT EDIT
import { renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  const _component_q_scroll_area = _resolveComponent("q-scroll-area")

  return (_openBlock(), _createBlock(_component_q_scroll_area, {
    ref: "qRef",
    onScroll: _ctx.onScroll
  }, {
    default: _withCtx(() => [
      _renderSlot(_ctx.$slots, "default")
    ]),
    _: 3 /* FORWARDED */
  }, 8 /* PROPS */, ["onScroll"]))
},
  data() {
    return {
      shouldScroll: true,
      lastHeight: NaN,
    };
  },
  updated() {
    if (this.shouldScroll) {
      this.$nextTick(() => this.$refs.qRef.setScrollPosition("vertical", Number.MAX_SAFE_INTEGER));
    }
  },
  methods: {
    onScroll(info) {
      if (info.verticalContainerSize === 0 || info.horizontalContainerSize === 0) return;
      if (info.verticalContainerSize !== this.lastHeight) {
        this.lastHeight = info.verticalContainerSize;
        return;
      }
      this.shouldScroll = this.$refs.qRef.getScroll().verticalPercentage === 1.0;
    },
  },
};
