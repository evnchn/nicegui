// AUTO-GENERATED from editor.js — DO NOT EDIT
import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  render(_ctx, _cache) {
  const _component_q_editor = _resolveComponent("q-editor")

  return (_openBlock(), _createBlock(_component_q_editor, {
    ref: "qRef",
    id: _ctx.id,
    modelValue: _ctx.inputValue,
    "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((_ctx.inputValue) = $event))
  }, _createSlots({ _: 2 /* DYNAMIC */ }, [
    _renderList(_ctx.$slots, (_, slot) => {
      return {
        name: slot,
        fn: _withCtx((slotProps) => [
          _renderSlot(_ctx.$slots, slot, _normalizeProps(_guardReactiveProps(slotProps || {})))
        ])
      }
    })
  ]), 1032 /* PROPS, DYNAMIC_SLOTS */, ["id", "modelValue"]))
},
  props: {
    value: String,
    id: String,
  },
  data() {
    return {
      inputValue: this.value,
      emitting: true,
    };
  },
  beforeUnmount() {
    const element = mounted_app.elements[this.$props.id.slice(1)];
    if (element) element.props.value = this.inputValue;
  },
  watch: {
    value(newValue) {
      this.emitting = false;
      this.inputValue = newValue;
      this.$nextTick(() => (this.emitting = true));
    },
    inputValue(newValue) {
      if (!this.emitting) return;
      this.$emit("update:value", newValue);
    },
  },
  methods: {
    updateValue() {
      this.inputValue = this.value;
    },
  },
};
