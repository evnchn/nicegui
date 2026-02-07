"""Tests to verify strict CSP works without violations."""
import pytest

from nicegui import ui
from nicegui.testing import Screen


@pytest.fixture(autouse=True)
def enable_csp_for_module(enable_csp):
    """Enable CSP for all tests in this module to verify CSP compatibility."""
    yield


def test_basic_elements_with_strict_csp(screen: Screen) -> None:
    """Test that basic UI elements work with strict CSP (no violations)."""
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
    screen.click('Click me')
    screen.should_contain('Clicked!')


def test_quasar_classes_work(screen: Screen) -> None:
    """Test that Quasar classes work with strict CSP."""
    @ui.page('/')
    def page():
        # Quasar classes should still work
        ui.label('Bold text').classes('text-weight-bold')
        ui.button('Primary').classes('q-pa-md')

    screen.open('/')
    screen.should_contain('Bold text')


def test_custom_css_works(screen: Screen) -> None:
    """Test that custom CSS added during page build works with strict CSP."""
    @ui.page('/')
    def page():
        # Static HTML added during page build gets nonces automatically
        ui.add_head_html('<style>.csp-works {color: green; font-weight: bold;}</style>')
        ui.label('CSP Compatible!').classes('csp-works')

    screen.open('/')
    label = screen.find('CSP Compatible!')
    # The style should be applied
    assert label.value_of_css_property('color') == 'rgba(0, 128, 0, 1)'
    assert label.value_of_css_property('font-weight') == '700'


def test_no_tailwind_classes_needed(screen: Screen) -> None:
    """Verify that the app works without Tailwind (Quasar classes work fine)."""
    @ui.page('/')
    def page():
        # We use Quasar classes instead of Tailwind when CSP is enabled
        ui.label('Bold text').classes('text-weight-bold text-h5')
        ui.label('Colored text').classes('text-primary')

    screen.open('/')
    screen.should_contain('Bold text')
    screen.should_contain('Colored text')


def test_dynamic_content_works(screen: Screen) -> None:
    """Test that dynamically added content works with strict CSP."""
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


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
