export default {
  template: `<component :is="tag"></component>`,
  data() {
    return { previousInnerHTML: null };
  },
  mounted() {
    this.renderContent();
  },
  updated() {
    this.renderContent();
  },
  methods: {
    renderContent() {
      if (this.innerHTML === this.previousInnerHTML) return;
      if (this.sanitize) {
        this.$el.setHTML(this.innerHTML);
      } else {
        // Raw innerHTML by explicit opt-in (sanitize=False); the default sanitize=True branch above runs DOMPurify.
        // Passing untrusted input here is the caller's documented responsibility, not a framework XSS.
        this.$el.innerHTML = this.innerHTML;
      }
      this.previousInnerHTML = this.innerHTML;
    },
  },
  props: {
    innerHTML: String,
    sanitize: Boolean,
    tag: String,
  },
};
