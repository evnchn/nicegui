import { Sortable } from "nicegui-sortable";

export default {
  template: "<div><slot></slot></div>",
  props: {
    options: Object,
  },
  mounted() {
    this.createSortable();
  },
  methods: {
    createSortable() {
      if (this.sortable) {
        this.sortable.destroy();
      }
      this.sortable = Sortable.create(this.$el, {
        ...this.options,
        onEnd: (evt) => {
          this.$emit("sort_end", {
            oldIndex: evt.oldIndex,
            newIndex: evt.newIndex,
            item_id: parseInt(evt.item.id.replace("c", "")),
            from_id: parseInt(evt.from.id.replace("c", "")),
            to_id: parseInt(evt.to.id.replace("c", "")),
          });
        },
      });
    },
    update_sortable(options) {
      if (this.sortable) {
        for (const [key, value] of Object.entries(options || {})) {
          this.sortable.option(key, value);
        }
      }
    },
    destroy_sortable() {
      if (this.sortable) {
        this.sortable.destroy();
        this.sortable = null;
      }
    },
    enable_sortable() {
      if (this.sortable) {
        this.sortable.option("disabled", false);
      }
    },
    disable_sortable() {
      if (this.sortable) {
        this.sortable.option("disabled", true);
      }
    },
    get_order() {
      if (this.sortable) {
        return this.sortable.toArray();
      }
      return [];
    },
  },
  beforeUnmount() {
    if (this.sortable) {
      this.sortable.destroy();
    }
  },
};
