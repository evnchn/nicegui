"""Test to capture and fail on CSP violations in the browser console.

This test helps detect CSP issues during development by checking browser console logs
for CSP violation errors.
"""
import pytest

from nicegui import ui
from nicegui.testing import Screen

from .csp_helpers import check_for_csp_violations


@pytest.fixture(autouse=True)
def enable_csp_for_module(enable_csp):
    """Enable CSP for all tests in this module to verify CSP compatibility."""
    yield


def test_basic_page_no_violations(screen: Screen) -> None:
    """Test that a basic page has no CSP violations."""
    @ui.page('/')
    def page():
        ui.label('Hello CSP!').classes('test-label')
        ui.button('Click me', on_click=lambda: ui.notify('Clicked!'))

    screen.open('/')
    screen.should_contain('Hello CSP!')

    violations = check_for_csp_violations(screen, 'basic_page')
    assert len(violations) == 0, f'Found {len(violations)} CSP violations on basic page'


def test_quasar_classes_no_violations(screen: Screen) -> None:
    """Test that Quasar classes work without CSP violations (Tailwind is auto-disabled)."""
    @ui.page('/')
    def page():
        ui.label('Bold text').classes('text-weight-bold text-h5')
        ui.label('Colored text').classes('text-primary')
        ui.button('Primary').classes('q-pa-md')

    screen.open('/')
    screen.should_contain('Bold text')

    violations = check_for_csp_violations(screen, 'quasar_classes')
    assert len(violations) == 0, f'Found {len(violations)} CSP violations with Quasar classes'


def test_add_head_html_no_violations(screen: Screen) -> None:
    """Test that add_head_html doesn't cause CSP violations."""
    @ui.page('/')
    def page():
        ui.add_head_html('<style>.csp-test {color: green; font-weight: bold;}</style>')
        ui.label('Styled text').classes('csp-test')

    screen.open('/')
    screen.should_contain('Styled text')

    violations = check_for_csp_violations(screen, 'add_head_html')
    assert len(violations) == 0, f'Found {len(violations)} CSP violations with add_head_html'


def test_button_click_no_violations(screen: Screen) -> None:
    """Test that button clicks don't cause CSP violations."""
    @ui.page('/')
    def page():
        ui.button('Click me', on_click=lambda: ui.notify('Clicked!'))

    screen.open('/')
    screen.click('Click me')
    screen.should_contain('Clicked!')

    violations = check_for_csp_violations(screen, 'button_click')
    assert len(violations) == 0, f'Found {len(violations)} CSP violations after button click'


def test_dynamic_content_no_violations(screen: Screen) -> None:
    """Test that dynamically added content doesn't cause CSP violations."""
    @ui.page('/')
    def page():
        container = ui.column()

        def add_label():
            with container:
                ui.label('New label')

        ui.button('Add label', on_click=add_label)

    screen.open('/')
    screen.click('Add label')
    screen.should_contain('New label')

    violations = check_for_csp_violations(screen, 'dynamic_content')
    assert len(violations) == 0, f'Found {len(violations)} CSP violations with dynamic content'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
