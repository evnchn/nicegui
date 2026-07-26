import pytest
from selenium.webdriver.common.by import By

from nicegui import ui
from nicegui.dependencies import (
    _SPECIFIER_PATTERN,
    component_query,
    generate_resources,
    js_components,
    resolve_component_source,
    vue_components,
)
from nicegui.testing import Screen, User


def test_component_sources_have_no_bare_specifiers(user: User):
    for key, component in list(js_components.items()) + list(vue_components.items()):
        source = resolve_component_source(key)
        if source is None:
            source = component.path.read_text(encoding='utf-8') if key in js_components else component.script
        for match in _SPECIFIER_PATTERN.finditer(source):
            specifier = match.group(2)
            assert specifier.startswith(('.', '/', 'http')), f'bare specifier "{specifier}" in {component.name}'


def test_importmap_override_changes_the_component_url(user: User):
    """A component's URL must change with its resolved source, or a cached client keeps the stale one."""
    assert component_query() == ''
    ui.aggrid.set_module_source('https://cdn.example.com/aggrid.js')
    key = next(key for key, component in js_components.items() if component.name == 'aggrid')
    assert component_query() != ''
    assert '"https://cdn.example.com/aggrid.js"' in resolve_component_source(key)


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
    """Elements added after the page has rendered must work although the importmap lists no ESM modules."""
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
