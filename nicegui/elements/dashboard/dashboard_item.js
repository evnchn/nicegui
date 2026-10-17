export default {
  template: `<div class="grid-stack-item"><div class="grid-stack-item-content"><slot></slot></div></div>`,
  props: {
    options: Object,
    revision: Number,
  },
  mounted() {
    Object.defineProperty(this.$el, "serverOptions", { get: () => this.options });
    this.writeAttributes();
    this.$el.parentElement?.gridstack?.makeWidget(this.$el);
  },
  beforeUnmount() {
    this.$el.parentElement?.gridstack?.removeWidget(this.$el, false);
  },
  methods: {
    writeAttributes() {
      this.$el.revision = this.revision; // reported with every geometry event so the server can drop stale ones
      for (const [key, value] of Object.entries(this.options)) {
        const name = "gs-" + key.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
        if (value === null || value === undefined || value === false) this.$el.removeAttribute(name);
        else this.$el.setAttribute(name, String(value));
      }
    },
  },
  watch: {
    revision() {
      // only server changes bump the revision, so geometry the browser reported itself is not applied again
      const grid = this.$el.parentElement?.gridstack;
      if (!grid) return this.writeAttributes(); // GridStack will read the attributes when it initializes
      if (!grid.pendingItems) {
        grid.pendingItems = new Map();
        queueMicrotask(() => flush(grid)); // apply all changes of one server update in a single batch
      }
      grid.pendingItems.set(this.$el, this);
    },
  },
};

function flush(grid) {
  const items = [...grid.pendingItems.values()];
  delete grid.pendingItems;
  grid.batchUpdate();
  for (const item of items) {
    const { x, y, ...rest } = item.options; // null min/max clear a limit, null x/y keep the current position
    item.$el.revision = item.revision;
    grid.update(item.$el, { ...rest, ...(x === null ? {} : { x }), ...(y === null ? {} : { y }) });
  }
  grid.batchUpdate(false);
  for (const item of items) {
    const node = item.$el.gridstackNode; // GridStack may pack or clip the update without emitting a change event
    if (node && ["x", "y", "w", "h"].some((key) => item.options[key] !== null && item.options[key] !== node[key]))
      item.$emit("geometry_sync", { x: node.x, y: node.y, w: node.w, h: node.h, revision: item.revision });
  }
}
