export function applyColors(colors) {
  const quasarColors = ["primary", "secondary", "accent", "dark", "dark-page", "positive", "negative", "info", "warning"];
  let customCSS = "";
  for (let color in colors) {
    if (quasarColors.includes(color))
      continue;
    const colorName = color.replaceAll("_", "-");
    const colorVar = "--q-" + colorName;
    document.body.style.setProperty(colorVar, colors[color]);
    customCSS += `.text-${colorName} { color: var(${colorVar}) !important; }\n`;
    customCSS += `.bg-${colorName} { background-color: var(${colorVar}) !important; }\n`;
  }
  if (!customCSS) return;
  const style = document.createElement("style");
  style.innerHTML = customCSS;
  style.dataset.niceguiCustomColors = "";
  document.head.querySelectorAll("[data-nicegui-custom-colors]").forEach((el) => el.remove());
  document.getElementsByTagName("head")[0].appendChild(style);
}
