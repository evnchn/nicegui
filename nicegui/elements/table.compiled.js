// AUTO-GENERATED from table.js — DO NOT EDIT
import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, openBlock as _openBlock, createBlock as _createBlock } from "vue"
import { convertDynamicProperties } from "../../static/utils/dynamic_properties.js";

export default {
  render(_ctx, _cache) {
  const _component_q_table = _resolveComponent("q-table")

  return (_openBlock(), _createBlock(_component_q_table, {
    ref: "qRef",
    columns: _ctx.convertedColumns,
    onFullscreen: _ctx.setFullscreenClass
  }, _createSlots({ _: 2 /* DYNAMIC */ }, [
    _renderList(_ctx.$slots, (_, slot) => {
      return {
        name: slot,
        fn: _withCtx((slotProps) => [
          _renderSlot(_ctx.$slots, slot, _normalizeProps(_guardReactiveProps(slotProps || {})))
        ])
      }
    })
  ]), 1032 /* PROPS, DYNAMIC_SLOTS */, ["columns", "onFullscreen"]))
},
  props: {
    columns: Array,
  },
  computed: {
    convertedColumns() {
      this.columns.forEach((column) => convertDynamicProperties(column, false));
      return this.columns;
    },
  },
  unmounted() {
    // Ensure the fullscreen scroll-behavior class does not linger on <html> if the
    // table is destroyed while fullscreen.
    document.documentElement.classList.remove("nicegui-table-fullscreen");
  },
  methods: {
    setFullscreenClass(isFullscreen) {
      // NOTE: prevent the page from smooth-scrolling when the table exits fullscreen;
      // Quasar uses setTimeout(() => el.scrollIntoView()) in exitFullscreen,
      // so we need a setTimeout to remove the class after that scroll completes.
      if (isFullscreen) {
        document.documentElement.classList.add("nicegui-table-fullscreen");
      } else {
        setTimeout(() => document.documentElement.classList.remove("nicegui-table-fullscreen"));
      }
    },
  },
};
