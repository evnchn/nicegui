export default {
  template: `
    <q-tab-panels ref="qRef" v-bind="$attrs" keep-alive>
      <template v-for="(_, slot) in $slots" v-slot:[slot]="slotProps">
        <slot :name="slot" v-bind="slotProps || {}" />
      </template>
    </q-tab-panels>
  `,
  inheritAttrs: false,
  async mounted() {
    const id = this.$el.id.slice(1);
    const elements = this.$root.$data.elements;
    const element = elements[id];
    const childIds = element.slots?.default?.ids || [];
    const names = childIds.map((cid) => elements[cid]?.props?.name).filter(Boolean);
    if (names.length <= 1) return;
    const qRef = this.$refs.qRef;
    const wasAnimated = qRef.animated;
    qRef.$.props.animated = false;
    const original = element.props["model-value"];
    for (const name of names) {
      element.props["model-value"] = name;
      await Vue.nextTick();
    }
    element.props["model-value"] = original;
    await Vue.nextTick();
    qRef.$.props.animated = wasAnimated;
  },
};
