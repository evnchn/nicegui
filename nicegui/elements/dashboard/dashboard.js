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
    this.grid = GridStack.init({ ...this.options }, this.$el);
    this.grid.on("change", (_, items) => {
      this.$emit(
        "layout_change",
        items.map((item) => ({ id: parseInt(item.el.id.substring(1)), x: item.x, y: item.y, w: item.w, h: item.h })),
      );
    });
  },
  unmounted() {
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
