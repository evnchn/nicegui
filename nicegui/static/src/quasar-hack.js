// HACK: remove Quasar's rules for divs in QCard (#2265, #2301)
for (const importRule of document.styleSheets[0].cssRules) {
  if (importRule instanceof CSSImportRule && /quasar/.test(importRule.styleSheet?.href)) {
    for (const rule of Array.from(importRule.styleSheet.cssRules)) {
      if (rule instanceof CSSStyleRule && /\.q-card > div/.test(rule.selectorText)) {
        if (/\.q-card > div/.test(rule.selectorText)) rule.selectorText = ".nicegui-card-tight" + rule.selectorText;
      }
    }
  }
}
