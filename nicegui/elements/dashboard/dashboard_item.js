export default {
  template: `<div class="grid-stack-item"><div class="grid-stack-item-content"><slot></slot></div></div>`,
  props: {
    options: Object,
  },
  mounted() {
    for (const [key, value] of Object.entries(this.options)) {
      if (value !== null && value !== undefined) this.$el.setAttribute(`gs-${toKebab(key)}`, String(value));
    }
    this.$el.parentElement?.gridstack?.makeWidget(this.$el);
  },
  beforeUnmount() {
    this.$el.parentElement?.gridstack?.removeWidget(this.$el, false);
  },
  watch: {
    options: {
      deep: true,
      handler(options) {
        this.$el.parentElement?.gridstack?.update(
          this.$el,
          Object.fromEntries(Object.entries(options).filter(([, value]) => value !== null)),
        );
      },
    },
  },
};

function toKebab(key) {
  return key.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
}
