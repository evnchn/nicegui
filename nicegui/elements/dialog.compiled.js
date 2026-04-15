// AUTO-GENERATED from dialog.js — DO NOT EDIT
import { renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  const _component_q_dialog = _resolveComponent("q-dialog")

  return (_openBlock(), _createBlock(_component_q_dialog, {
    onShow: _ctx.addClass,
    onHide: _ctx.removeClass
  }, {
    default: _withCtx(() => [
      _renderSlot(_ctx.$slots, "default")
    ]),
    _: 3 /* FORWARDED */
  }, 8 /* PROPS */, ["onShow", "onHide"]))
},
  methods: {
    addClass() {
      // NOTE: prevent the page from scrolling when the dialog is closed (#5031)
      document.documentElement.classList.add("nicegui-dialog-open");
    },
    removeClass() {
      document.documentElement.classList.remove("nicegui-dialog-open");
    },
  },
  unmounted() {
    this.removeClass();
  },
};
