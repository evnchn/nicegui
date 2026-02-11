import { normalizeProps as _normalizeProps, guardReactiveProps as _guardReactiveProps, renderSlot as _renderSlot, resolveComponent as _resolveComponent, withCtx as _withCtx, renderList as _renderList, createSlots as _createSlots, openBlock as _openBlock, createBlock as _createBlock } from "vue"

export default {
  props: ["options"],
  render(_ctx, _cache) {
  const _component_q_select = _resolveComponent("q-select")

  return (_openBlock(), _createBlock(_component_q_select, {
    ref: "qRef",
    options: _ctx.filteredOptions,
    onFilter: _ctx.filterFn,
    onPopupShow: _ctx.addClass,
    onPopupHide: _ctx.removeClass
  }, _createSlots({ _: 2 /* DYNAMIC */ }, [
    _renderList(_ctx.$slots, (_, slot) => {
      return {
        name: slot,
        fn: _withCtx((slotProps) => [
          _renderSlot(_ctx.$slots, slot, _normalizeProps(_guardReactiveProps(slotProps || {})))
        ])
      }
    })
  ]), 1032 /* PROPS, DYNAMIC_SLOTS */, ["options", "onFilter", "onPopupShow", "onPopupHide"]))
},
  data() {
    return {
      initialOptions: this.options,
      filteredOptions: this.options,
    };
  },
  methods: {
    filterFn(val, update, abort) {
      update(() => (this.filteredOptions = val ? this.findFilteredOptions() : this.initialOptions));
    },
    findFilteredOptions() {
      const needle = this.$el.querySelector("input[type=search]")?.value.toLocaleLowerCase();
      return needle
        ? this.initialOptions.filter((v) => String(v.label).toLocaleLowerCase().indexOf(needle) > -1)
        : this.initialOptions;
    },
    addClass() {
      // NOTE: prevent the page from scrolling when the select popup is closed (#5031)
      document.documentElement.classList.add("nicegui-select-popup-open");
    },
    async removeClass() {
      await this.$nextTick();
      document.documentElement.classList.remove("nicegui-select-popup-open");
    },
  },
  updated() {
    if (!this.$attrs.multiple) return;
    const newFilteredOptions = this.findFilteredOptions();
    if (newFilteredOptions.length !== this.filteredOptions.length) {
      this.filteredOptions = newFilteredOptions;
    }
  },
  unmounted() {
    this.removeClass();
  },
  watch: {
    options: {
      handler(newOptions) {
        this.initialOptions = newOptions;
        this.filteredOptions = newOptions;
      },
      immediate: true,
    },
  },
};
