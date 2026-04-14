// AUTO-GENERATED from expansion.js — DO NOT EDIT
import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, createElementVNode as _createElementVNode, resolveComponent as _resolveComponent, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, openBlock as _openBlock, createBlock as _createBlock } from "vue"

const _hoisted_1 = { class: "nicegui-expansion-content" }

export default {
  render(_ctx, _cache) {
  const _component_q_expansion_item = _resolveComponent("q-expansion-item")

  return (_openBlock(), _createBlock(_component_q_expansion_item, { ref: "qRef" }, _createSlots({
    default: _withCtx(() => [
      _createElementVNode("div", _hoisted_1, [
        _renderSlot(_ctx.$slots, "default")
      ])
    ]),
    _: 2 /* DYNAMIC */
  }, [
    _renderList(_ctx.nonDefaultSlots, (_, name) => {
      return {
        name: name,
        fn: _withCtx((slotProps) => [
          _renderSlot(_ctx.$slots, name, _normalizeProps(_guardReactiveProps(slotProps || {})))
        ])
      }
    })
  ]), 1536 /* NEED_PATCH, DYNAMIC_SLOTS */))
},
  computed: {
    nonDefaultSlots() {
      const { default: _, ...rest } = this.$slots;
      return rest;
    },
  },
};
