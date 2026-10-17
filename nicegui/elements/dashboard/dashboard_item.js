export default {
  template: `<div class="grid-stack-item"><div class="grid-stack-item-content"><slot></slot></div></div>`,
  props: {
    options: Object,
  },
  mounted() {
    this.writeAttributes();
    this.$el.parentElement?.gridstack?.makeWidget(this.$el);
  },
  beforeUnmount() {
    this.$el.parentElement?.gridstack?.removeWidget(this.$el, false);
  },
  methods: {
    writeAttributes() {
      for (const [key, value] of Object.entries(this.options)) {
        const name = "gs-" + key.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
        if (value === null || value === undefined || value === false) this.$el.removeAttribute(name);
        else this.$el.setAttribute(name, String(value));
      }
    },
  },
  watch: {
    options: {
      deep: true,
      handler(options) {
        const grid = this.$el.parentElement?.gridstack;
        if (!grid) return this.writeAttributes(); // GridStack will read the attributes when it initializes
        const { x, y, ...rest } = options; // null min/max clear a limit, null x/y keep the current position
        grid.update(this.$el, { ...rest, ...(x === null ? {} : { x }), ...(y === null ? {} : { y }) });
        const node = this.$el.gridstackNode; // GridStack may pack or clip the update without emitting a change event
        if (node && ["x", "y", "w", "h"].some((key) => options[key] !== null && options[key] !== node[key]))
          this.$emit("geometry_sync", { x: node.x, y: node.y, w: node.w, h: node.h });
      },
    },
  },
};
