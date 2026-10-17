import { GridStack } from "nicegui-dashboard";
import { loadResource } from "../../static/utils/resources.js";

export default {
  template: `<div class="grid-stack"><slot></slot></div>`,
  props: {
    options: Object,
    resourcePath: String,
  },
  async mounted() {
    await this.$nextTick(); // wait for window.path_prefix to be set
    await loadResource(window.path_prefix + `${this.resourcePath}/gridstack.min.css`);
    if (this.disposed) return;
    this.grid = GridStack.init({ ...this.options }, this.$el);
    const geometry = (items) =>
      items.map((item) => ({
        id: parseInt(item.el.id.substring(1)),
        ...{ x: item.x, y: item.y, w: item.w, h: item.h },
        revision: item.el.revision,
      }));
    const echo = (item) => ["x", "y", "w", "h"].every((key) => this.grid.applying?.get(item.el)?.[key] === item[key]);
    this.grid.on("change", (_, items) => {
      items = items.filter((item) => !echo(item)); // skip tiles that just applied exactly what the server sent
      if (items.length) this.$emit("layout_change", geometry(items));
    });
    const startGesture = (el) => (this.grid.gesture = el.gridstackNode); // server updates wait, a batch would hide this gesture's change
    const stopGesture = () => {
      delete this.grid.gesture;
      queueMicrotask(() => this.grid.flushAfterGesture?.()); // runs after GridStack reported the gesture's change
    };
    this.grid.on("dragstart", (_, el) => startGesture(el));
    this.grid.on("dragstop", stopGesture);
    this.grid.on("removed", (_, items) => items.includes(this.grid.gesture) && stopGesture()); // deleted or dropped elsewhere
    this.grid.on("resizestart", (_, el) => {
      startGesture(el);
      this.resizeStart = { w: el.gridstackNode.w, h: el.gridstackNode.h };
    });
    this.grid.on("resizestop", (_, el) => {
      stopGesture();
      const node = el.gridstackNode;
      if (node.w !== this.resizeStart?.w || node.h !== this.resizeStart?.h) this.$emit("item_resize", geometry([node]));
    });
    this.grid.on("added", (_, items) => this.$emit("layout_sync", geometry(items)));
    this.$emit("layout_sync", geometry(this.grid.engine.nodes));
  },
  beforeUnmount() {
    this.disposed = true;
    this.grid?.destroy(false);
  },
  watch: {
    options: {
      deep: true,
      handler(options) {
        if (!this.grid) return;
        this.grid.setStatic(Boolean(options.staticGrid));
        this.grid.float(Boolean(options.float));
        if (options.column !== this.grid.getColumn()) this.grid.column(options.column);
        if (options.cellHeight !== undefined) this.grid.cellHeight(options.cellHeight);
      },
    },
  },
};
