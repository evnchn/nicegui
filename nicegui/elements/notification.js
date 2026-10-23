import { convertDynamicProperties } from "../../static/utils/dynamic_properties.js";

export default {
  mounted() {
    this.ready = Quasar.loadPlugin("Notify").then((Notify) => {
      this.notification = Notify.create(this.convertedOptions);
    });
  },
  methods: {
    update_notification() {
      this.ready.then(() => this.notification(this.convertedOptions));
    },
    dismiss() {
      this.ready.then(() => this.notification());
    },
  },
  computed: {
    convertedOptions() {
      convertDynamicProperties(this.options, true);
      const options = {
        ...this.options,
        onDismiss: () => this.$emit("dismiss"),
      };
      return options;
    },
  },
  props: {
    options: Object,
  },
};
