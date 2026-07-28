from pathlib import Path

import pytest
from selenium.webdriver.common.by import By

from nicegui import ui
from nicegui.dependencies import (
    _SPECIFIER_PATTERN,
    _component_source,
    component_query,
    generate_resources,
    js_components,
    resolve_component_source,
    vue_components,
)
from nicegui.testing import Screen, User


def test_component_sources_have_no_bare_specifiers(user: User):
    for key, component in list(js_components.items()) + list(vue_components.items()):
        source = resolve_component_source(key) or _component_source(key)
        assert source is not None
        for match in _SPECIFIER_PATTERN.finditer(source):
            specifier = match.group('specifier')
            assert specifier.startswith(('.', '/', 'http')), f'bare specifier "{specifier}" in {component.name}'


def test_importmap_override_changes_the_component_url(user: User):
    assert component_query() == ''
    ui.aggrid.set_module_source('https://cdn.example.com/aggrid.js')
    key = next(key for key, component in js_components.items() if component.name == 'aggrid')
    assert component_query() != ''
    assert '"https://cdn.example.com/aggrid.js"' in resolve_component_source(key)


def test_esm_module_registered_after_render(screen: Screen, tmp_path: Path):
    module_dir = tmp_path / 'dist'
    module_dir.mkdir()
    (module_dir / 'index.js').write_text('export const LABEL = "late module loaded";')

    component_path = tmp_path / 'late.js'
    component_path.write_text('''
        import { LABEL } from "nicegui-late";
        export default {
            template: "<div>{{ text }}</div>",
            data() {
                return { text: LABEL };
            },
        };
    ''')

    @ui.page('/')
    def page():
        def create():
            # an element whose module is only registered now, i.e. after this page's importmap was sent
            class LateElement(ui.element, component=str(component_path), esm={'nicegui-late': str(module_dir)}):
                pass
            LateElement()
        ui.button('Create', on_click=create)

    screen.open('/')
    screen.click('Create')
    screen.should_contain('late module loaded')


@pytest.mark.parametrize('path,expected', [('/plain', []), ('/esm', ['nicegui-mermaid', 'nicegui-mermaid/'])])
async def test_importmap_only_lists_esm_modules_of_rendered_elements(user: User, path: str, expected: list[str]):
    @ui.page('/plain')
    def plain():
        ui.label('hello')

    @ui.page('/esm')
    def esm():
        ui.mermaid('graph TD; Node_A --> Node_B;')

    client = await user.open(path)
    imports = generate_resources('', client.elements.values())[3]
    assert [key for key in imports if key.startswith('nicegui-')] == expected


@pytest.mark.parametrize('element', ['echart', 'mermaid', 'codemirror'])
def test_create_dynamically_without_importmap(screen: Screen, element: str):
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
