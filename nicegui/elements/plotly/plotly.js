import { convertDynamicProperties } from "../../static/utils/dynamic_properties.js";

const bundles = {};
const traceTypes = new WeakMap();

function tracesOf(value) {
  if (Array.isArray(value)) return value;
  if (value?.data || value?.frames) {
    return [...(value.data ?? []), ...(value.frames ?? []).flatMap((frame) => frame?.data ?? [])];
  }
  return [value];
}

function loadBundle(full) {
  const specifier = full ? "nicegui-plotly/full.js" : "nicegui-plotly";
  bundles[specifier] ??= import(specifier).then(({ Plotly }) => {
    traceTypes.set(Plotly, new Set(Object.keys(Plotly.PlotSchema.get().traces)));
    return Plotly;
  });
  return bundles[specifier];
}

export default {
  template: "<div></div>",
  async mounted() {
    this.full_loaded = this.full;
    this.Plotly = await loadBundle(this.full);
    this.update();
    this.$nextTick(() => {
      this.resizeObserver = new ResizeObserver(() => {
        if (this.options.config?.responsive === false) return;
        this.Plotly.Plots.resize(this.$el);
      });
      this.resizeObserver.observe(this.$el);
    });
  },
  unmounted() {
    this.resizeObserver?.disconnect();
  },
  methods: {
    update() {
      // wait for plotly to be loaded
      if (typeof this.Plotly === "undefined") {
        setTimeout(this.update, 10);
        return;
      }

      // swap in the full bundle if the figure uses a trace type the loaded one does not know
      if (this.needs_full_bundle(this.options)) {
        this.upgrade().then(this.update);
        return;
      }

      // default responsive to true
      const options = this.options;
      if (options.config?.responsive === true) options.config.responsive = undefined;

      // reuse plotly instance if config is the same
      let promise;
      if (this.last_options && JSON.stringify(options.config) === JSON.stringify(this.last_options.config)) {
        promise = this.Plotly.react(this.$el, this.options, options.config);
      } else {
        promise = this.Plotly.newPlot(this.$el, this.options, options.config);
        this.set_handlers();
      }

      // store last options
      this.last_options = options;
      return promise;
    },
    needs_full_bundle(figure) {
      // an unregistered trace type is not an error in plotly.js, it silently renders as a scatter trace
      if (this.full_loaded) return false; // NOTE: a type the full bundle does not know either must not loop
      const known = traceTypes.get(this.Plotly);
      return tracesOf(figure).some((trace) => trace?.type !== undefined && !known.has(trace.type));
    },
    upgrade() {
      this.upgrading ??= (async () => {
        const light = this.Plotly;
        this.Plotly = await loadBundle(true);
        this.full_loaded = true;
        if (this.last_options) light.purge(this.$el); // the light bundle's plot state is not the full one's to reuse
        this.last_options = null;
      })();
      return this.upgrading;
    },
    async run_plot_method(name, ...args) {
      if (typeof this.Plotly === "undefined") {
        logAndEmit("error", "Plotly is not loaded yet.");
        return;
      }
      // methods taking trace data take it as their first argument, so that is the only one worth checking
      if (this.needs_full_bundle(args[0])) {
        await this.upgrade();
        await this.update();
      }
      convertDynamicProperties(args, true);
      const result = await runMethod(this.Plotly, name, [this.$el, ...args]);
      // most plotly.js functions resolve to the graph element, which cannot be serialized back to the server
      return result === this.$el ? undefined : result;
    },
    set_handlers() {
      // forward events
      for (const name of [
        // source: https://plotly.com/javascript/plotlyjs-events/
        "plotly_click",
        "plotly_legendclick",
        "plotly_selecting",
        "plotly_selected",
        "plotly_hover",
        "plotly_unhover",
        "plotly_legenddoubleclick",
        "plotly_restyle",
        "plotly_relayout",
        "plotly_webglcontextlost",
        "plotly_afterplot",
        "plotly_autosize",
        "plotly_deselect",
        "plotly_doubleclick",
        "plotly_redraw",
        "plotly_animated",
      ]) {
        this.$el.on(name, (event) => {
          const args = {
            ...event,
            points: event?.points?.map((p) => ({
              ...p,
              fullData: undefined,
              xaxis: undefined,
              yaxis: undefined,
            })),
            xaxes: undefined,
            yaxes: undefined,
          };
          this.$emit(name, args);
        });
      }
    },
  },
  data() {
    return {
      last_options: null,
      upgrading: null,
      full_loaded: false,
    };
  },
  props: {
    options: Object,
    full: Boolean,
  },
};
