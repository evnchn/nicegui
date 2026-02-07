#!/usr/bin/env python3
"""Test UnoCSS with STRICT CSP to demonstrate it has the same issue as Tailwind."""
import pytest

from nicegui import core, ui
from nicegui.testing import Screen


@pytest.fixture(autouse=True)
def enable_strict_csp(enable_csp):  # pylint: disable=unused-argument
    """Enable CSP with STRICT settings - no unsafe-inline.

    This fixture removes 'unsafe-inline' from the CSP to test if UnoCSS
    runtime can work with strict CSP (spoiler: it can't, just like Tailwind).
    """
    import secrets  # pylint: disable=import-outside-toplevel

    from nicegui import middlewares  # pylint: disable=import-outside-toplevel

    original_dispatch = middlewares.CSPMiddleware.dispatch

    async def strict_dispatch(self, request, call_next):  # pylint: disable=unused-argument
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        if core.app.config.csp_enabled and response.headers.get('X-NiceGUI-Content') == 'page':
            # STRICT CSP - NO unsafe-inline!
            csp_directives = [
                f"script-src 'nonce-{nonce}' 'strict-dynamic'",
                f"style-src 'self' 'nonce-{nonce}",  # REMOVED unsafe-inline
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


@pytest.fixture(autouse=True)
def enable_unocss():
    """Enable UnoCSS for this test module.

    Note: This requires restarting the NiceGUI app with unocss='wind4'
    For a real test, you would run with:
        ui.run(unocss='wind4', csp_enabled=True)
    """
    # This is a placeholder - in reality you'd need to configure this
    # at app startup with ui.run(unocss='wind4')
    yield


@pytest.mark.skip(reason='Requires UnoCSS configuration (ui.run(unocss="wind4")) - demonstration test only')
def test_unocss_basic_with_strict_csp(screen: Screen):
    """Test basic UnoCSS classes with strict CSP.

    Expected: UnoCSS runtime will generate <style> tags without nonces,
    which will be blocked by strict CSP.
    """
    @ui.page('/')
    def page():
        ui.label('Red text').classes('text-red-500')
        ui.label('Bold text').classes('font-bold')
        ui.button('Primary').classes('bg-blue-500 text-white px-4 py-2')

    screen.open('/')
    screen.should_contain('Red text')
    screen.should_contain('Bold text')

    # Check for CSP violations
    logs = screen.selenium.get_log('browser')
    csp_violations = [
        log for log in logs
        if 'Content-Security-Policy' in log.get('message', '')
        or 'Refused to apply' in log.get('message', '')
    ]

    print(f"\n{'='*60}")
    print('UnoCSS Runtime + Strict CSP Test Results')
    print(f"{'='*60}")
    print(f'Total browser logs: {len(logs)}')
    print(f'CSP Violations: {len(csp_violations)}')

    if csp_violations:
        print('\nSample violations:')
        for v in csp_violations[:3]:
            print(f"  [{v['level']}] {v['message'][:150]}")

    # Check if styles were applied
    try:
        label = screen.find('Red text')
        color = label.value_of_css_property('color')
        font_weight = screen.find('Bold text').value_of_css_property('font-weight')

        print('\nStyles applied:')
        print(f'  Red text color: {color}')
        print(f'  Bold text weight: {font_weight}')

        # With strict CSP, UnoCSS-generated styles should be blocked
        # So the color should NOT be red (rgb(239, 68, 68) or similar)
        if 'rgb(239, 68, 68)' in color or 'rgb(239,68,68)' in color:
            print('\n⚠️  WARNING: Styles were applied despite strict CSP!')
            print('   This means UnoCSS generated styles are NOT being blocked.')
        else:
            print('\n✅ EXPECTED: Styles were blocked by strict CSP')
            print("   UnoCSS runtime needs 'unsafe-inline' just like Tailwind JIT")
    except Exception as e:
        print(f'\nError checking styles: {e}')

    print(f"{'='*60}\n")


@pytest.mark.skip(reason='Requires UnoCSS configuration (ui.run(unocss="wind4")) - demonstration test only')
def test_unocss_dynamic_classes_with_strict_csp(screen: Screen):
    """Test dynamically added UnoCSS classes with strict CSP.

    This demonstrates that UnoCSS runtime watches for DOM changes
    and generates styles on-the-fly, which will be blocked by strict CSP.
    """
    @ui.page('/')
    def page():
        label = ui.label('Dynamic').props('id="dynamic-label"')
        ui.button('Add classes', on_click=lambda: label.classes('text-purple-600 text-3xl'))

    screen.open('/')

    # Get initial state
    label_elem = screen.selenium.find_element('id', 'dynamic-label')
    initial_color = label_elem.value_of_css_property('color')
    initial_size = label_elem.value_of_css_property('font-size')

    # Add classes dynamically
    screen.click('Add classes')
    screen.wait(0.5)

    # Check if styles were applied
    final_color = label_elem.value_of_css_property('color')
    final_size = label_elem.value_of_css_property('font-size')

    print(f"\n{'='*60}")
    print('UnoCSS Dynamic Classes Test')
    print(f"{'='*60}")
    print(f'Initial - Color: {initial_color}, Size: {initial_size}')
    print(f'Final   - Color: {final_color}, Size: {final_size}')

    if initial_color != final_color or initial_size != final_size:
        print('\n⚠️  Styles changed - UnoCSS runtime worked despite strict CSP')
    else:
        print('\n✅ Styles unchanged - UnoCSS runtime blocked by strict CSP')

    # Check for CSP violations
    logs = screen.selenium.get_log('browser')
    csp_violations = [
        log for log in logs
        if 'Content-Security-Policy' in log.get('message', '')
        or 'Refused to apply' in log.get('message', '')
    ]

    print(f'CSP Violations: {len(csp_violations)}')
    print(f"{'='*60}\n")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
