"""Test the CSP example to ensure it has no violations."""
import pytest

from nicegui import app, ui
from nicegui.testing import Screen


def test_csp_example_no_violations(screen: Screen) -> None:
    """Test that the CSP example page has no CSP violations."""
    # Enable CSP just like in the example
    original_csp = app.config.csp_enabled
    app.config.csp_enabled = True

    try:
        @ui.page('/')
        def page():
            ui.label('CSP Example').classes('text-2xl')
            ui.label('This page has CSP enabled!')

            # Static HTML added during page build works fine with CSP
            ui.add_head_html('<style>.csp-test {color: green; font-weight: bold;}</style>')
            ui.label('This text uses a style added via add_head_html()').classes('csp-test')

            # External scripts and styles work fine with CSP
            ui.button('Test Button', on_click=lambda: ui.notify('Button clicked!'))

        screen.open('/')
        screen.should_contain('CSP Example')
        screen.should_contain('This page has CSP enabled!')

        # Click the button to trigger JavaScript execution
        screen.click('Test Button')
        screen.should_contain('Button clicked!')

        # Check for CSP violations in browser console
        logs = screen.selenium.get_log('browser')

        csp_violations = [
            log for log in logs
            if 'Content-Security-Policy' in log.get('message', '')
            or 'Refused to' in log.get('message', '')
            or 'violates the following Content Security Policy' in log.get('message', '')
            or 'EvalError' in log.get('message', '')
        ]

        if csp_violations:
            print(f"\n{'='*70}")
            print('CSP VIOLATIONS DETECTED in example:')
            print(f"{'='*70}")
            for i, violation in enumerate(csp_violations, 1):
                level = violation.get('level', 'UNKNOWN')
                message = violation.get('message', 'No message')
                print(f'\n{i}. [{level}]')
                print(f'   {message[:500]}')
            print(f"{'='*70}\n")

        assert len(csp_violations) == 0, f'Found {len(csp_violations)} CSP violations in example'

    finally:
        app.config.csp_enabled = original_csp


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
