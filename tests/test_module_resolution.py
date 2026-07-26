import pytest
from selenium.webdriver.common.by import By

from nicegui import client as client_module
from nicegui import ui
from nicegui.dependencies import _SPECIFIER_PATTERN, js_components, resolve_component_source, vue_components
from nicegui.testing import Screen, User


def test_component_sources_have_no_bare_specifiers(user: User):
    for key, component in list(js_components.items()) + list(vue_components.items()):
        source = resolve_component_source(key)
        if source is None:
            source = component.path.read_text(encoding='utf-8') if key in js_components else component.script
        for match in _SPECIFIER_PATTERN.finditer(source):
            specifier = match.group(2)
            assert specifier.startswith(('.', '/', 'http')), f'bare specifier "{specifier}" in {component.name}'


@pytest.mark.parametrize('element', ['echart', 'mermaid', 'codemirror'])
def test_create_dynamically_without_importmap(screen: Screen, monkeypatch: pytest.MonkeyPatch, element: str):
    """Elements added after the page has rendered must work even if the importmap lists no ESM modules."""
    original = client_module.generate_resources

    def without_esm_modules(prefix, elements):
        vue_html, vue_styles, vue_scripts, imports, js_imports, js_imports_urls = original(prefix, elements)
        imports = {key: url for key, url in imports.items() if not key.startswith('nicegui-')}
        return vue_html, vue_styles, vue_scripts, imports, js_imports, js_imports_urls
    monkeypatch.setattr(client_module, 'generate_resources', without_esm_modules)

    @ui.page('/')
    def page():
        creators = {
            'echart': lambda: ui.echart({'xAxis': {'type': 'value'},
                                         'yAxis': {'type': 'category', 'data': ['A']},
                                         'series': [{'type': 'line', 'data': [0.1]}]}),
            'mermaid': lambda: ui.mermaid('graph TD; Node_A --> Node_B;'),
            'codemirror': lambda: ui.codemirror('print("hello")', language='Python'),
        }
        ui.button('Create', on_click=creators[element])

    screen.open('/')
    screen.click('Create')
    screen.should_not_contain('Failed to resolve module specifier')
    if element == 'echart':
        assert screen.find_by_tag('canvas')
    elif element == 'mermaid':
        assert screen.selenium.find_element(By.XPATH, '//span[p[contains(text(), "Node_B")]]')
    else:
        assert screen.find_by_class('cm-editor')
