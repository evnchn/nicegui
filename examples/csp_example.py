#!/usr/bin/env python3
"""Example demonstrating strict Content Security Policy (CSP) support in NiceGUI.

CSP is a security feature that helps prevent XSS attacks by controlling which resources
can be loaded and executed on a page.

IMPORTANT: When CSP is enabled, Tailwind is automatically disabled because Tailwind's
JIT compilation requires 'unsafe-inline' for styles, which is incompatible with strict CSP.

Instead, you can use Quasar's built-in utility classes or custom CSS.
"""
from nicegui import app, ui

# Enable strict CSP - this automatically disables Tailwind
app.config.csp_enabled = True

# Optionally add custom CSP directives
# app.config.csp_extra_directives = ["connect-src 'self' https://api.example.com"]


@ui.page('/')
def index():
    ui.label('Strict CSP Example').classes('text-h4')
    ui.label('This page has strict CSP enabled (Tailwind is auto-disabled)')

    # Quasar classes still work
    with ui.card().classes('q-pa-md'):
        ui.label('Card with Quasar classes').classes('text-weight-bold')
        ui.button('Test Button', on_click=lambda: ui.notify('Button clicked!'))

    # Custom CSS works too
    ui.add_head_html('<style>.custom-green {color: green; font-weight: bold;}</style>')
    ui.label('Custom styled text').classes('custom-green')

    ui.markdown('''
    ### CSP Configuration

    CSP is configured in your app startup code:

    ```python
    from nicegui import app

    # Enable strict CSP (auto-disables Tailwind)
    app.config.csp_enabled = True

    # Add custom directives (optional)
    app.config.csp_extra_directives = [
        "connect-src 'self' https://api.example.com"
    ]
    ```

    ### Current CSP Policy

    The strict CSP policy includes:
    - `script-src 'nonce-XXX' 'strict-dynamic' 'unsafe-eval'` - Scripts require nonces (unsafe-eval for Vue)
    - `style-src 'self' 'nonce-XXX'` - Styles from same origin or with nonce
    - `font-src 'self' data:` - Fonts from same origin and data URIs
    - `img-src 'self' data: https:` - Images from various sources
    - `object-src 'none'` - Block plugins
    - `base-uri 'none'` - Prevent base tag hijacking

    ### What Works

    - ✅ Quasar utility classes
    - ✅ Custom CSS via ui.add_head_html()
    - ✅ External stylesheets
    - ✅ All JavaScript functionality
    - ✅ Vue components

    ### What Doesn't Work

    - ❌ Tailwind classes (auto-disabled when CSP is enabled)
    - ❌ UnoCSS (also requires unsafe-inline)
    ''')


ui.run()
