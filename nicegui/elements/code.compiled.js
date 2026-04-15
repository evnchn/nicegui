// AUTO-GENERATED from code.js — DO NOT EDIT
import { renderSlot as _renderSlot, openBlock as _openBlock, createElementBlock as _createElementBlock } from "vue"

export default {
  render(_ctx, _cache) {
  return (_openBlock(), _createElementBlock("div", null, [
    _renderSlot(_ctx.$slots, "default")
  ]))
},
  mounted() {
    if (!navigator.clipboard) this.$el.querySelector(".q-btn").style.display = "none";
  },
  props: {
    content: String,
  },
};
