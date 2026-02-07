# CSP Strictness Analysis

## Current Status

Our CSP implementation uses **CSP-Lite** (permissive CSP) rather than **Strict CSP**.

## CSP Header Actually Sent

```
Content-Security-Policy:
  script-src 'nonce-{nonce}' 'strict-dynamic';
  style-src 'self' 'nonce-{nonce}' 'unsafe-inline';
  style-src-elem 'self' 'nonce-{nonce}' 'unsafe-inline';
  font-src 'self' data:;
  img-src 'self' data: https:;
  object-src 'none';
  base-uri 'none'
```

## The Problem: `'unsafe-inline'`

The directive `'unsafe-inline'` in `style-src` and `style-src-elem` **completely defeats CSP protection for styles**.

### What This Means

✅ **Protected:**
- Scripts - Cannot execute unless they have the correct nonce
- Inline event handlers (`onclick=`) - Blocked
- `eval()` and similar - Blocked

❌ **NOT Protected:**
- **Inline styles** - ANY inline style can be injected
- **Dynamic style injection** - `document.createElement('style')` works
- **CSS-based attacks** - Not protected
- **ui.add_css()** - Works without nonce (but shouldn't!)

### Proof

Test results show that dynamic style injection succeeds:

```python
# This SHOULD fail with strict CSP but DOESN'T
ui.run_javascript('''
    const style = document.createElement('style');
    style.textContent = '.malicious { color: red !important; }';
    document.head.appendChild(style);  // This succeeds!
''')
```

Color changes from black to red, proving the style was applied.

## Why Do We Use `'unsafe-inline'`?

### Stated Reason
The code comment says: "unsafe-inline for Tailwind JIT"

### The Tailwind JIT Issue

Tailwind JIT (Just-In-Time) works by:
1. Scanning the DOM for class names
2. Dynamically generating CSS
3. Injecting `<style>` tags into the document

These dynamically generated `<style>` tags need either:
- A nonce attribute (`<style nonce="...">`)
- OR `'unsafe-inline'` in the CSP

**Current approach:** We chose `'unsafe-inline'` as the easy solution.

**Problem:** This allows ALL inline styles, not just Tailwind's.

## Comparison with PR #5345

The original PR #5345 attempted stricter CSP and encountered:
- Vue template compiler issues (generating ES6 imports)
- Build system incompatibilities
- More test failures

Our implementation succeeds because we relaxed CSP with `'unsafe-inline'`.

## Security Implications

### What We Actually Get

Our CSP provides:
- ✅ XSS protection for **scripts**
- ✅ Protection against malicious `<script>` tags
- ❌ NO protection against **CSS injection**
- ❌ NO protection against inline style attacks

### Attack Surface Still Open

An attacker who can inject content could still:
1. Inject inline styles to hide/modify content
2. Use CSS-based data exfiltration
3. Create clickjacking with CSS positioning
4. Inject keyloggers via CSS attribute selectors

## Solutions

### Option 1: Keep Current (CSP-Lite)
**Pros:**
- Works with all NiceGUI features
- Simple implementation
- 64 test files pass

**Cons:**
- Not truly secure against CSS-based attacks
- Marketing as "CSP support" may be misleading

### Option 2: Strict CSP (Remove `'unsafe-inline'`)
**Pros:**
- True CSP protection
- Industry standard security

**Cons:**
- Tailwind JIT may break
- Would need to add nonces to dynamically generated styles
- More test failures expected
- Significant engineering effort

### Option 3: Conditional CSP
**Pros:**
- Let users choose security level
- `csp_mode='strict'` or `csp_mode='permissive'`

**Cons:**
- More complex configuration
- Tailwind might still break in strict mode

### Option 4: Replace Tailwind JIT
**Pros:**
- Could achieve strict CSP
- Better security

**Cons:**
- Major breaking change
- Would require build-time CSS generation

## Recommendations

### Immediate Actions

1. **Document the limitation clearly**
   - Add to CSP documentation that styles use `'unsafe-inline'`
   - Clarify this is "CSP-Lite" not "Strict CSP"
   - List what IS and ISN'T protected

2. **Update CSP_TEST_COVERAGE.md**
   - Add section about strictness limitations
   - Explain the Tailwind JIT tradeoff

3. **Consider renaming**
   - Instead of "CSP support", say "Partial CSP support"
   - Or "CSP for scripts (styles use unsafe-inline)"

### Long-term Solutions

1. **Investigate Tailwind alternatives**
   - Build-time Tailwind compilation
   - Pre-generate all possible classes
   - Switch to different CSS framework

2. **Add nonce to Tailwind-generated styles**
   - Monkey-patch Tailwind to add nonces
   - May require forking/modifying Tailwind

3. **Make CSP configurable**
   - Let security-conscious users disable Tailwind
   - Allow strict CSP mode for those who don't need JIT

## Conclusion

Our current CSP implementation is **not strict**. It provides script protection but allows inline styles. This is a reasonable tradeoff for compatibility with Tailwind JIT, but should be clearly documented as "Partial CSP" or "CSP-Lite" rather than implying full CSP protection.

The 55% test coverage is less impressive when we realize those tests pass because CSP is relaxed, not because the features are truly CSP-compatible.
