"""Test to capture and fail on CSP violations in the browser console.

This test helps detect CSP issues during development by checking browser console logs
for CSP violation errors.
"""
import pytest

from nicegui import ui
from nicegui.testing import Screen


@pytest.fixture(autouse=True)
def enable_csp_for_module(enable_csp):
    """Enable CSP for all tests in this module to verify CSP compatibility."""
    yield


def check_for_csp_violations(screen: Screen, page_name: str = "unknown") -> list:
    """Check browser console logs for CSP violations and return them.

    Args:
        screen: The Screen fixture
        page_name: Name of the page being tested (for better error messages)

    Returns:
        List of CSP violation log entries
    """
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
        print(f'CSP VIOLATIONS DETECTED on page: {page_name}')
        print(f"{'='*70}")
        print(f'Total browser logs: {len(logs)}')
        print(f'CSP Violations: {len(csp_violations)}')
        print('\nViolations:')
        for i, violation in enumerate(csp_violations, 1):
            level = violation.get('level', 'UNKNOWN')
            message = violation.get('message', 'No message')
            print(f"\n{i}. [{level}]")
            print(f"   {message[:500]}")
            if len(message) > 500:
                print("   ... (truncated)")
        print(f"{'='*70}\n")

    return csp_violations


def test_basic_page_no_violations(screen: Screen) -> None:
    """Test that a basic page has no CSP violations."""
    @ui.page('/')
    def page():
        ui.label('Hello CSP!').classes('test-label')
        ui.button('Click me', on_click=lambda: ui.notify('Clicked!'))

    screen.open('/')
    screen.should_contain('Hello CSP!')

    violations = check_for_csp_violations(screen, "basic_page")
    assert len(violations) == 0, f"Found {len(violations)} CSP violations on basic page"


def test_tailwind_classes_no_violations(screen: Screen) -> None:
    """Test that Tailwind classes don't cause CSP violations."""
    @ui.page('/')
    def page():
        ui.label('Red text').classes('text-red-500')
        ui.label('Bold text').classes('font-bold text-2xl')
        ui.button('Primary').classes('bg-blue-500 text-white px-4 py-2')

    screen.open('/')
    screen.should_contain('Red text')

    violations = check_for_csp_violations(screen, "tailwind_classes")
    assert len(violations) == 0, f"Found {len(violations)} CSP violations with Tailwind classes"


def test_add_head_html_no_violations(screen: Screen) -> None:
    """Test that add_head_html doesn't cause CSP violations."""
    @ui.page('/')
    def page():
        ui.add_head_html('<style>.csp-test {color: green; font-weight: bold;}</style>')
        ui.label('Styled text').classes('csp-test')

    screen.open('/')
    screen.should_contain('Styled text')

    violations = check_for_csp_violations(screen, "add_head_html")
    assert len(violations) == 0, f"Found {len(violations)} CSP violations with add_head_html"


def test_button_click_no_violations(screen: Screen) -> None:
    """Test that button clicks don't cause CSP violations."""
    @ui.page('/')
    def page():
        ui.button('Click me', on_click=lambda: ui.notify('Clicked!'))

    screen.open('/')
    screen.click('Click me')
    screen.should_contain('Clicked!')

    violations = check_for_csp_violations(screen, "button_click")
    assert len(violations) == 0, f"Found {len(violations)} CSP violations after button click"


def test_dynamic_content_no_violations(screen: Screen) -> None:
    """Test that dynamically added content doesn't cause CSP violations."""
    @ui.page('/')
    def page():
        container = ui.column()

        def add_label():
            with container:
                ui.label('New label').classes('text-green-500')

        ui.button('Add label', on_click=add_label)

    screen.open('/')
    screen.click('Add label')
    screen.should_contain('New label')

    violations = check_for_csp_violations(screen, "dynamic_content")
    assert len(violations) == 0, f"Found {len(violations)} CSP violations with dynamic content"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
