# Strict CSP Implementation for NiceGUI

This document describes the strict Content Security Policy (CSP) implementation in NiceGUI.

## Overview

This implementation provides **strict CSP support** that helps prevent XSS attacks by controlling which resources can be loaded and executed on a page. When CSP is enabled, Tailwind is automatically disabled because it's incompatible with strict CSP.

## Key Features

- **Nonce-based CSP**: Every request gets a unique cryptographic nonce for inline scripts and styles
- **Automatic Tailwind disable**: Tailwind is auto-disabled when CSP is enabled (it requires 'unsafe-inline')
- **No CSP violations**: All inline scripts and styles have proper nonces
- **No unsafe-eval**: Uses Vue runtime-only build with pre-compiled templates and CSP-safe script injection
- **Configurable**: Add custom CSP directives via `app.config.csp_extra_directives`

## Implementation Details

### 1. CSPMiddleware (`nicegui/middlewares.py`)

- Generates a cryptographically secure nonce for each request
- Stores nonce in `request.state.csp_nonce`
- Sets CSP headers only for HTML page responses
- Policy includes:
  - `script-src 'nonce-XXX' 'strict-dynamic'`
  - `style-src 'self' 'nonce-XXX'`
  - `style-src-elem 'self' 'nonce-XXX'`
  - Additional security directives

### 2. Vue Runtime-Only Build

- Uses `vue.runtime.esm-browser.js` (excludes template compiler, ~30% smaller)
- All 32 component templates pre-compiled to render functions at build time via `compile_templates.js`
- `@vue/compiler-dom` shipped separately for runtime compilation of dynamic templates (slots, VBuild, third-party)
- `cspSafeEval()` replaces all `eval()`/`new Function()` calls using dynamic `<script>` element injection

### 3. Template Updates (`nicegui/templates/index.html`)

All inline `<script>` and `<style>` tags now have conditional nonces:
```html
<script{% if csp_nonce %} nonce="{{ csp_nonce }}"{% endif %}>
  // script content
</script>
```

The `addStyle` helper also propagates nonces to dynamically created styles:
```javascript
addStyle = (c) => document.head.append(Object.assign(document.createElement("style"),
  { textContent: c{% if csp_nonce %}, nonce: "{{ csp_nonce }}"{% endif %} }));
```

### 4. Client Updates (`nicegui/client.py`)

The `build_response` method retrieves the nonce from request state and passes it to the template:
```python
csp_nonce = getattr(request.state, 'csp_nonce', '')
context = {
    ...
    'csp_nonce': csp_nonce,
}
```

### 5. Configuration (`nicegui/app/app_config.py`)

Added CSP configuration options:
```python
csp_enabled: bool = False  # Disabled by default
csp_extra_directives: list[str] = field(default_factory=list)
```

When CSP is enabled, Tailwind and UnoCSS are automatically disabled in `add_run_config`.

## Usage

### Basic Usage

```python
from nicegui import app, ui

# Enable strict CSP
app.config.csp_enabled = True

@ui.page('/')
def index():
    # Use Quasar classes instead of Tailwind
    ui.label('Hello').classes('text-h4 text-primary')
    ui.button('Click me', on_click=lambda: ui.notify('Clicked!'))

ui.run()
```

### With Custom Directives

```python
from nicegui import app, ui

app.config.csp_enabled = True
app.config.csp_extra_directives = [
    "connect-src 'self' https://api.example.com",
    "frame-ancestors 'none'"
]

ui.run()
```

### In Tests

```python
import pytest
from nicegui.testing import Screen

@pytest.fixture(autouse=True)
def enable_csp_for_module(enable_csp):
    """Enable CSP for all tests in this module."""
    yield

def test_with_csp(screen: Screen):
    @ui.page('/')
    def page():
        ui.label('Test')

    screen.open('/')
    screen.should_contain('Test')
```

## What Works

- All JavaScript functionality
- Vue components
- Quasar utility classes
- Custom CSS via `ui.add_head_html()`
- External stylesheets
- Dynamic content updates

## What Doesn't Work

- Tailwind CSS classes (auto-disabled when CSP is enabled)
- UnoCSS (also requires 'unsafe-inline')
- Any framework that injects inline styles without nonces

## Security Considerations

### No unsafe-eval

The implementation does **not** require `'unsafe-eval'`. All JavaScript evaluation is done via CSP-safe dynamic `<script>` element injection, which is permitted by `'strict-dynamic'`. Vue component templates are pre-compiled at build time, and dynamic templates use `@vue/compiler-dom` with `cspSafeEval()`.

### Style Security

Styles require nonces, providing protection against CSS injection attacks. The trade-off is that Tailwind JIT cannot be used because it dynamically generates styles without nonces.

## Testing

Run CSP tests:
```bash
python -m pytest tests/test_strict_csp.py -v
```

All tests should pass without CSP violations in the browser console.

## Files Changed

1. `nicegui/middlewares.py` - Added CSPMiddleware
2. `nicegui/templates/index.html` - Added nonces to all inline scripts/styles, added compiler-dom import
3. `nicegui/client.py` - Pass nonce to template
4. `nicegui/app/app_config.py` - Added CSP configuration
5. `nicegui/ui_run.py` - Register CSPMiddleware
6. `nicegui/testing/general_fixtures.py` - Added enable_csp fixture
7. `nicegui/testing/plugin.py` - Export enable_csp fixture
8. `examples/csp_example.py` - Example demonstrating CSP
9. `tests/test_strict_csp.py` - Tests verifying CSP works without violations
10. `nicegui/static/nicegui.js` - Added cspSafeEval, compileVueTemplate, runJavascript rewrite
11. `compile_templates.js` - Build script to pre-compile Vue component templates
12. `nicegui/static/utils/dynamic_properties.js` - Uses cspSafeEval instead of eval

## Future Improvements

1. **Pre-compiled Tailwind**: Generate a static Tailwind CSS file at build time
2. **CSP Reporting**: Add support for CSP violation reporting
3. **Configurable Strictness**: Allow users to choose between strict CSP and Tailwind support
