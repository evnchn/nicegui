// AUTO-GENERATED from input.js — DO NOT EDIT
import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, resolveComponent as _resolveComponent, withKeys as _withKeys, mergeProps as _mergeProps, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, createVNode as _createVNode, Fragment as _Fragment, openBlock as _openBlock, createElementBlock as _createElementBlock, createCommentVNode as _createCommentVNode } from "vue"

const _hoisted_1 = ["id"]
const _hoisted_2 = ["value"]

export default {
  render(_ctx, _cache) {
  const _component_q_input = _resolveComponent("q-input")

  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createVNode(_component_q_input, _mergeProps({ ref: "qRef" }, _ctx.$attrs, {
      modelValue: _ctx.inputValue,
      "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((_ctx.inputValue) = $event)),
      "shadow-text": _ctx.shadowText,
      onKeydown: _withKeys(_ctx.perform_autocomplete, ["tab"]),
      list: _ctx.id + '-datalist'
    }), _createSlots({ _: 2 /* DYNAMIC */ }, [
      _renderList(_ctx.$slots, (_, slot) => {
        return {
          name: slot,
          fn: _withCtx((slotProps) => [
            _renderSlot(_ctx.$slots, slot, _normalizeProps(_guardReactiveProps(slotProps || {})))
          ])
        }
      })
    ]), 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["modelValue", "shadow-text", "onKeydown", "list"]),
    (_ctx.withDatalist)
      ? (_openBlock(), _createElementBlock("datalist", {
          key: 0,
          id: _ctx.id + '-datalist'
        }, [
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(this._autocomplete, (option) => {
            return (_openBlock(), _createElementBlock("option", { value: option }, null, 8 /* PROPS */, _hoisted_2))
          }), 256 /* UNKEYED_FRAGMENT */))
        ], 8 /* PROPS */, _hoisted_1))
      : _createCommentVNode("v-if", true)
  ], 64 /* STABLE_FRAGMENT */))
},
  props: {
    _autocomplete: Array,
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
  computed: {
    shadowText() {
      if (!this.inputValue) return "";
      const matchingOption = this._autocomplete.find((option) =>
        option.toLowerCase().startsWith(this.inputValue.toLowerCase()),
      );
      return matchingOption ? matchingOption.slice(this.inputValue.length) : "";
    },
    withDatalist() {
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      return isMobile && this._autocomplete && this._autocomplete.length > 0;
    },
  },
  methods: {
    updateValue() {
      this.inputValue = this.value;
    },
    perform_autocomplete(e) {
      if (this.shadowText) {
        this.inputValue += this.shadowText;
        e.preventDefault();
      }
    },
  },
};
