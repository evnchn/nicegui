from pathlib import Path

from nicegui import ui
from nicegui.dependencies import (
    _SPECIFIER_PATTERN,
    _component_source,
    component_query,
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
