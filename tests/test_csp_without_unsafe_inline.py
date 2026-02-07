#!/usr/bin/env python3
"""Test with STRICT CSP - removing 'unsafe-inline'."""
import pytest
from nicegui import ui, core
from nicegui.testing import Screen


@pytest.fixture(autouse=True)
def enable_strict_csp(enable_csp):
    """Enable CSP with STRICT settings - no unsafe-inline."""
    # Monkey-patch the CSP middleware to remove unsafe-inline
    from nicegui import middlewares
    import secrets

    original_dispatch = middlewares.CSPMiddleware.dispatch

    async def strict_dispatch(self, request, call_next):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        if core.app.config.csp_enabled and response.headers.get('X-NiceGUI-Content') == 'page':
            # STRICT CSP - NO unsafe-inline!
            csp_directives = [
                f"script-src 'nonce-{nonce}' 'strict-dynamic'",
                f"style-src 'self' 'nonce-{nonce}'",  # REMOVED unsafe-inline
                f"style-src-elem 'self' 'nonce-{nonce}'",  # REMOVED unsafe-inline
                "font-src 'self' data:",
                "img-src 'self' data: https:",
                "object-src 'none'",
                "base-uri 'none'",
            ]

            if core.app.config.csp_extra_directives:
                csp_directives.extend(core.app.config.csp_extra_directives)

            response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        return response

    middlewares.CSPMiddleware.dispatch = strict_dispatch

    yield

    # Restore original
    middlewares.CSPMiddleware.dispatch = original_dispatch


def test_basic_elements_with_strict_csp(screen: Screen):
    """Test that basic elements work with STRICT CSP (no unsafe-inline)."""
    @ui.page('/')
    def page():
        ui.label('Hello CSP!').classes('test-label')
        ui.button('Click me', on_click=lambda: ui.notify('Clicked!'))
        with ui.row():
            ui.label('Row 1')
            ui.label('Row 2')

    screen.open('/')
    screen.should_contain('Hello CSP!')
    screen.should_contain('Click me')

    # Check for CSP violations
    logs = screen.selenium.get_log('browser')
    csp_violations = [log for log in logs if 'Content-Security-Policy' in log.get('message', '')]

    print(f"\nCSP Violations: {len(csp_violations)}")
    for v in csp_violations[:5]:
        print(f"  {v['message'][:200]}")

    # The test might pass but we should see CSP violations in console


def test_tailwind_classes_with_strict_csp(screen: Screen):
    """Test if Tailwind JIT works with strict CSP.

    This is the key question - does Tailwind JIT need unsafe-inline?
    """
    @ui.page('/')
    def page():
        ui.label('Red text').classes('text-red-500')
        ui.label('Bold text').classes('font-bold')
        ui.button('Primary').classes('bg-blue-500')

    screen.open('/')
    screen.should_contain('Red text')
    screen.should_contain('Bold text')

    # Check if styles are applied
    label = screen.find('Red text')

    # Check console
    logs = screen.selenium.get_log('browser')
    print(f"\nTotal browser logs: {len(logs)}")

    csp_violations = [log for log in logs if 'Content-Security-Policy' in log.get('message', '')]
    print(f"CSP Violations: {len(csp_violations)}")
    for v in csp_violations[:5]:
        print(f"  {v['level']}: {v['message'][:200]}")


def test_dynamic_style_blocked_with_strict_csp(screen: Screen):
    """Verify that dynamic style injection is NOW blocked."""
    @ui.page('/')
    def page():
        ui.label('Test').props('id="test-label"')
        ui.button('Inject style', on_click=lambda: ui.run_javascript('''
            const style = document.createElement('style');
            style.textContent = '#test-label { color: red !important; }';
            document.head.appendChild(style);
        '''))

    screen.open('/')

    label = screen.selenium.find_element('id', 'test-label')
    initial_color = label.value_of_css_property('color')
    print(f"\nInitial color: {initial_color}")

    screen.click('Inject style')
    screen.wait(0.5)

    final_color = label.value_of_css_property('color')
    print(f"Final color: {final_color}")

    # Check console
    logs = screen.selenium.get_log('browser')
    csp_violations = [log for log in logs if 'Content-Security-Policy' in log.get('message', '') or 'Refused to apply' in log.get('message', '')]

    print(f"\nCSP Violations: {len(csp_violations)}")
    for v in csp_violations[:3]:
        print(f"  {v['level']}: {v['message'][:200]}")

    if initial_color == final_color:
        print("\n✓ GOOD: Dynamic style injection was BLOCKED by strict CSP")
    else:
        print("\n✗ BAD: Dynamic style injection still succeeded")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
