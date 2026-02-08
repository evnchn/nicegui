"""Test the CSP example to ensure it has no violations."""
import pytest

from nicegui import app, ui
from nicegui.testing import Screen

from .csp_helpers import check_for_csp_violations


def test_csp_example_no_violations(screen: Screen) -> None:
    """Test that the CSP example page has no CSP violations."""
    original_csp = app.config.csp_enabled
    app.config.csp_enabled = True

    try:
        @ui.page('/')
        def page():
            ui.label('CSP Example').classes('text-h4')
            ui.label('This page has CSP enabled!')

            ui.add_head_html('<style>.csp-test {color: green; font-weight: bold;}</style>')
            ui.label('This text uses a style added via add_head_html()').classes('csp-test')

            ui.button('Test Button', on_click=lambda: ui.notify('Button clicked!'))

        screen.open('/')
        screen.should_contain('CSP Example')
        screen.should_contain('This page has CSP enabled!')

        screen.click('Test Button')
        screen.should_contain('Button clicked!')

        violations = check_for_csp_violations(screen, 'csp_example')
        assert len(violations) == 0, f'Found {len(violations)} CSP violations in example'

    finally:
        app.config.csp_enabled = original_csp


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
