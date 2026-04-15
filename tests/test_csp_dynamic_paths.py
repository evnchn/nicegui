"""Empirical verification that cspSafeEval paths do not trigger CSP violations.

Targets Copilot's concern that `cspSafeEval` and `document.createElement('script')`
lack explicit nonces under a `script-src 'nonce-...' 'strict-dynamic'` policy.
If strict-dynamic delegates trust correctly, scripts created by trusted (nonce'd)
code execute without their own nonce.
"""
import pytest

from nicegui import ui
from nicegui.testing import Screen

from .csp_helpers import check_for_csp_violations


@pytest.fixture(autouse=True)
def enable_csp_for_module(enable_csp):
    yield


def test_run_javascript_no_csp_violations(screen: Screen):
    """ui.run_javascript() → dynamic <script> via cspSafeEval path."""
    @ui.page('/')
    def page():
        ui.button('run', on_click=lambda: ui.run_javascript('window.__rj = 42'))

    screen.open('/')
    screen.click('run')
    screen.wait(0.5)
    assert not check_for_csp_violations(screen, page_name='run_javascript')


def test_dynamic_prop_no_csp_violations(screen: Screen):
    """Dynamic `:valueFormatter` prop → cspSafeEval path in convertDynamicProperties."""
    @ui.page('/')
    def page():
        ui.aggrid({
            'columnDefs': [{'field': 'name', ':valueFormatter': '(p) => `[${p.value}]`'}],
            'rowData': [{'name': 'Alice'}],
        })

    screen.open('/')
    screen.wait(1)
    assert not check_for_csp_violations(screen, page_name='dynamic_prop')


def test_js_handler_no_csp_violations(screen: Screen):
    """js_handler= on event → cspSafeEval path in parseEvents."""
    @ui.page('/')
    def page():
        ui.button('click').on('click', js_handler='(e) => { window.__jh = e.type; }')

    screen.open('/')
    screen.click('click')
    screen.wait(0.5)
    assert not check_for_csp_violations(screen, page_name='js_handler')
