export default {
  template: `<div><slot v-if="shouldRender"></slot></div>`,
  data() {
    return {
      shouldRender: false,
    };
  },
  mounted() {
    // nextTick + double rAF: wait until Vue has flushed and the browser has painted the
    // surrounding UI, so rendering the heavy subtree does not block first paint.
    this.$nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          this.shouldRender = true;
        });
      });
    });
  },
};
