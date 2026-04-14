// AUTO-GENERATED from teleport.js — DO NOT EDIT
import { renderSlot as _renderSlot, Teleport as _Teleport, openBlock as _openBlock, createBlock as _createBlock, createCommentVNode as _createCommentVNode } from "vue"

export default {
  render(_ctx, _cache) {
  return (_ctx.isLoaded)
    ? (_openBlock(), _createBlock(_Teleport, {
        to: _ctx.to,
        key: _ctx.key
      }, [
        _renderSlot(_ctx.$slots, "default")
      ], 8 /* PROPS */, ["to"]))
    : _createCommentVNode("v-if", true)
},
  props: {
    to: String,
  },
  mounted() {
    this.isLoaded = true;
  },
  data() {
    return {
      key: 0,
      isLoaded: false,
    };
  },
  methods: {
    update() {
      this.key++;
    },
  },
};
