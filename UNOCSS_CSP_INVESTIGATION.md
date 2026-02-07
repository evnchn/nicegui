# UnoCSS and CSP Investigation

## Question
Can UnoCSS help remove the dependency on `'unsafe-inline'` in our CSP implementation?

## TL;DR Answer
**No, not in runtime mode.** UnoCSS runtime has the exact same CSP issue as Tailwind JIT. However, UnoCSS build-time mode could potentially solve this problem.

---

## Background

Our current CSP implementation requires `'unsafe-inline'` for styles because Tailwind JIT dynamically injects `<style>` tags into the DOM at runtime. This defeats CSP protection for styles.

## How UnoCSS Works

UnoCSS offers **two modes of operation**:

### 1. Runtime Mode (Current NiceGUI Implementation)
- Loaded via CDN: `preset-wind4.global.js` + `core.global.js`
- Runs directly in the browser
- Uses MutationObserver to detect DOM changes
- Dynamically generates and injects CSS on the fly
- Injects styles using: `<style data-unocss-runtime-layer="default">`

**CSP Impact:** Runtime mode has the **same problem** as Tailwind JIT - it dynamically injects `<style>` tags that need either:
- `'unsafe-inline'` in CSP (current approach, defeats CSP protection)
- OR nonces on every dynamically created style tag (not currently supported)

### 2. Build-Time Mode (Not Currently Used)
- Integrated with build tools (Vite, Webpack, etc.)
- Generates static CSS files at build time
- No runtime DOM injection

**CSP Impact:** Build-time mode would be **compatible with strict CSP** because all CSS is pre-generated as static files.

---

## Current NiceGUI Implementation

**Configuration:** [nicegui/app/app_config.py](nicegui/app/app_config.py)
```python
tailwind: bool = field(init=False)
unocss: Literal['mini', 'wind3', 'wind4'] | None = field(init=False)
```

**Template:** [nicegui/templates/index.html](nicegui/templates/index.html) (lines 57-79)
```html
{% if unocss %}
<script nonce="{{ csp_nonce }}" defer src="/_nicegui/.../static/unocss/preset-{{unocss}}.global.js"></script>
<script nonce="{{ csp_nonce }}">
  window.__unocss = {
    presets: [
      () => window.__unocss_runtime.presets.preset{{unocss.title()}}({...}),
    ],
    runtime: { ready: () => false },
    outputToCssLayers: {...},
  };
</script>
<script nonce="{{ csp_nonce }}" defer src="/_nicegui/.../static/unocss/core.global.js"></script>
{% endif %}
```

**This is runtime mode** - UnoCSS generates CSS dynamically in the browser.

---

## Comparison: Tailwind JIT vs UnoCSS Runtime

| Aspect | Tailwind JIT | UnoCSS Runtime |
|--------|-------------|----------------|
| **Style Generation** | Dynamic (browser) | Dynamic (browser) |
| **DOM Injection** | Yes (`<style>` tags) | Yes (`<style data-unocss-runtime-layer>` tags) |
| **CSP Requirement** | `'unsafe-inline'` OR nonces | `'unsafe-inline'` OR nonces |
| **Performance** | Slower | 5-200x faster (claimed) |
| **CSP Compatible?** | ❌ Not in runtime mode | ❌ Not in runtime mode |

**Key Finding:** Both frameworks suffer from the **same fundamental CSP issue** when used in runtime mode.

---

## Why UnoCSS Doesn't Solve the Problem (Yet)

### Search Results

I searched for:
- "UnoCSS Content Security Policy CSP nonce strict compatibility"
- "UnoCSS vs Tailwind JIT dynamic style injection CSP"
- "UnoCSS runtime mode how styles generated DOM injection"

**Findings:**
1. ✅ UnoCSS documentation confirms it uses [runtime DOM injection](https://unocss.dev/integrations/runtime)
2. ✅ [Runtime discussion #80](https://github.com/unocss/unocss/discussions/80) confirms dynamic style generation
3. ❌ No documentation on CSP nonce support for runtime-generated styles
4. ❌ No GitHub issues discussing UnoCSS + strict CSP compatibility
5. ⚠️ Similar frameworks (styled-components, CSS-in-JS) have [CSP compatibility issues](https://github.com/orgs/styled-components/discussions/3942)

### UnoCSS Runtime Behavior

According to [official documentation](https://unocss.dev/integrations/runtime):
- "Runs UnoCSS right in the browser"
- "Detects DOM changes to generate styles on the fly"
- Uses `<style data-unocss-runtime-layer="default">` tags
- Regenerates CSS on every DOM mutation

**Problem:** These dynamically created `<style>` tags don't have nonces, so they require `'unsafe-inline'`.

---

## Potential Solutions

### Option 1: Keep Current Setup (Runtime Mode + `'unsafe-inline'`)

**Status Quo** - Continue using UnoCSS or Tailwind in runtime mode.

**Pros:**
- Works with all NiceGUI features
- No breaking changes
- Easy to maintain

**Cons:**
- Not truly secure (CSS injection possible)
- CSP is "CSP-Lite" not "Strict CSP"

---

### Option 2: Switch to Build-Time CSS Generation

**Major Change** - Generate all CSS at build time instead of runtime.

#### How It Would Work:
1. **Pre-scan** all NiceGUI components and examples
2. **Generate** a comprehensive CSS file containing all used classes
3. **Serve** this static CSS file (compatible with strict CSP)
4. **Disable** runtime JIT compilation

**Pros:**
- ✅ Compatible with strict CSP (no `'unsafe-inline'`)
- ✅ Potentially faster (no runtime overhead)
- ✅ True XSS protection for styles

**Cons:**
- ❌ No dynamic class generation (breaks user-provided arbitrary classes)
- ❌ Requires build step changes
- ❌ May miss classes used in dynamic content
- ❌ Larger initial CSS bundle

**Example of what would break:**
```python
# This works with runtime JIT:
ui.label('Hello').classes('text-[#f4a261]')  # Arbitrary color

# With build-time only, this would fail unless pre-generated
```

---

### Option 3: Patch UnoCSS Runtime to Support Nonces

**Custom Solution** - Modify UnoCSS runtime to add nonces to generated `<style>` tags.

#### Implementation:
1. Fork UnoCSS or use monkey-patching
2. Intercept style tag creation
3. Add `nonce` attribute from `window.__csp_nonce__`
4. Submit upstream PR to UnoCSS

**Pros:**
- ✅ Maintains runtime flexibility
- ✅ Strict CSP compatibility
- ✅ No breaking changes for users

**Cons:**
- ⚠️ Requires maintenance of fork/patch
- ⚠️ No guarantee upstream accepts PR
- ⚠️ Complex to implement correctly

**Example patch (conceptual):**
```javascript
// In UnoCSS runtime, when creating style tags:
const style = document.createElement('style');
style.setAttribute('data-unocss-runtime-layer', 'default');
// ADD THIS:
if (window.__csp_nonce__) {
  style.setAttribute('nonce', window.__csp_nonce__);
}
document.head.appendChild(style);
```

---

### Option 4: Hybrid Approach

**Pragmatic** - Build-time for core, runtime for user extensions.

#### Strategy:
1. **Build-time CSS** for all NiceGUI elements and common Tailwind classes
2. **Runtime mode** available but requires explicit opt-in
3. **Documentation** clearly states CSP implications

**Configuration:**
```python
ui.run(
    csp_enabled=True,
    csp_strict=True,  # New flag: disables runtime CSS
)
```

**Pros:**
- ✅ Strict CSP available for security-conscious users
- ✅ Runtime mode still available for those who need it
- ✅ Clear tradeoffs documented

**Cons:**
- ⚠️ More complex configuration
- ⚠️ Users may not understand implications

---

## Recommendations

### Immediate (No Code Changes)

1. **✅ Already Done:** Document that CSP uses `'unsafe-inline'` (see [CSP_STRICTNESS_ANALYSIS.md](CSP_STRICTNESS_ANALYSIS.md))
2. **Update documentation** to clarify that both Tailwind and UnoCSS have the same CSP limitation in runtime mode
3. **Add note to UnoCSS configuration** explaining CSP implications

### Short-Term (Minor Changes)

1. **Investigate nonce patching**
   - Test if monkey-patching UnoCSS runtime to add nonces works
   - Create proof-of-concept
   - Measure performance impact

2. **Open GitHub issue with UnoCSS**
   - Request native nonce support for CSP compatibility
   - Share findings from this investigation
   - Link to NiceGUI use case

### Long-Term (Major Changes)

1. **Implement build-time CSS option**
   - Add `ui.run(css_mode='build'|'runtime')` configuration
   - Generate comprehensive CSS from NiceGUI elements
   - Allow strict CSP for build-time mode

2. **Create safelist approach**
   - Similar to PurgeCSS safelist
   - Pre-generate common patterns
   - Allow dynamic classes only for non-CSP mode

---

## Conclusion

**UnoCSS does NOT solve the CSP `'unsafe-inline'` problem when used in runtime mode** (the current NiceGUI implementation). The issue is not Tailwind-specific - it's inherent to ANY runtime CSS generation that dynamically injects `<style>` tags.

### The Core Problem
Runtime CSS frameworks (Tailwind JIT, UnoCSS runtime) need to create `<style>` tags on-the-fly. These tags require either:
- `'unsafe-inline'` in CSP (defeats CSP protection) ← **Current approach**
- Nonces on every created tag (not currently supported by UnoCSS runtime)

### Possible Paths Forward
1. **Accept CSP-Lite** - Document limitations, keep current approach
2. **Patch UnoCSS** - Add nonce support to runtime style injection
3. **Build-time CSS** - Generate static CSS, achieve strict CSP
4. **Make it configurable** - Let users choose security vs. flexibility

---

## Sources

- [UnoCSS Runtime Documentation](https://unocss.dev/integrations/runtime)
- [UnoCSS GitHub Repository](https://github.com/unocss/unocss)
- [Why UnoCSS?](https://unocss.dev/guide/why)
- [UnoCSS Runtime Discussion #80](https://github.com/unocss/unocss/discussions/80)
- [Tailwind CSP Discussion #13326](https://github.com/tailwindlabs/tailwindcss/discussions/13326)
- [Content Security Policy Guide](https://content-security-policy.com/nonce/)
- [MDN: CSP style-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/style-src)
- [CSS-in-JS and CSP Article](https://medium.com/cyberark-engineering/when-css-in-js-and-csp-collide-e9547474a2cb)
- [styled-components CSP Discussion](https://github.com/orgs/styled-components/discussions/3942)
