from selenium.webdriver.common.by import By

from nicegui import __version__, ui
from nicegui.testing import Screen


def test_dev_mode(screen: Screen) -> None:
    screen.ui_run_kwargs['prod_js'] = False

    @ui.page('/')
    def page():
        ui.label('Hello, world!')

    screen.open('/')
    importmap = screen.selenium.find_element(By.XPATH, '//script[@type="importmap"]')
    importmap_html = importmap.get_attribute('innerHTML') or ''
    assert f'/_nicegui/{__version__}/static/vue.esm-browser.js' in importmap_html
    assert f'/_nicegui/{__version__}/static/quasar.esm.js' in importmap_html
    js_logs = screen.render_js_logs()
    warnings = [w for w in js_logs.split('\n') if 'Vue warn' in w and 'Hydration' not in w]
    assert not warnings, f'Unexpected Vue warnings: {warnings}'


def test_prod_mode(screen: Screen):
    screen.ui_run_kwargs['prod_js'] = True

    @ui.page('/')
    def page():
        ui.label('Hello, world!')

    screen.open('/')
    importmap = screen.selenium.find_element(By.XPATH, '//script[@type="importmap"]')
    importmap_html = importmap.get_attribute('innerHTML') or ''
    assert f'/_nicegui/{__version__}/static/vue.esm-browser.prod.js' in importmap_html
    assert f'/_nicegui/{__version__}/static/quasar.esm.prod.js' in importmap_html
    assert 'Vue warn' not in screen.render_js_logs()
