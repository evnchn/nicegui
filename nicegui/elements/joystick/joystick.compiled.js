// AUTO-GENERATED from joystick.js — DO NOT EDIT
import { createElementVNode as _createElementVNode, openBlock as _openBlock, createElementBlock as _createElementBlock } from "vue"
import { nipplejs } from "nicegui-joystick";

export default {
  render(_ctx, _cache) {
  return (_openBlock(), _createElementBlock("div", null, [...(_cache[0] || (_cache[0] = [
    _createElementVNode("div", null, null, -1 /* CACHED */)
  ]))]))
},
  mounted() {
    const joystick = nipplejs.create({
      zone: this.$el.children[0],
      position: { left: "50%", top: "50%" },
      dynamicPage: true,
      ...this.options,
    });
    joystick.on("start", (e) => this.$emit("start", e));
    joystick.on("move", (_, data) => this.$emit("move", { data }));
    joystick.on("end", (e) => this.$emit("end", e));
  },
  props: {
    options: Object,
  },
};
