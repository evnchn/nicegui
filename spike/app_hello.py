"""Hello-world page + a page that adds heavy components dynamically after load."""
import sys

from nicegui import ui

PORT = int(sys.argv[1])


@ui.page('/')
def hello() -> None:
    ui.label('Hello world')


@ui.page('/dyn')
def dyn() -> None:
    ui.label('Hello world')
    container = ui.column()

    def add() -> None:
        with container:
            ui.table(columns=[{'name': 'a', 'label': 'A', 'field': 'a'}], rows=[{'a': 1}, {'a': 2}])
            with ui.tabs() as tabs:
                ui.tab('One')
                ui.tab('Two')
            with ui.tab_panels(tabs, value='One'):
                with ui.tab_panel('One'):
                    ui.label('panel one')
            with ui.stepper().props('vertical'):
                with ui.step('First'):
                    ui.label('step one')
                    with ui.stepper_navigation():
                        ui.button('Next')
    ui.button('add', on_click=add).mark('addbtn')


@ui.page('/rich')
def rich() -> None:
    ui.label('Hello world')
    ui.table(columns=[{'name': 'a', 'label': 'A', 'field': 'a'}], rows=[{'a': 1}, {'a': 2}])
    with ui.tabs() as tabs:
        ui.tab('One')
        ui.tab('Two')
    with ui.tab_panels(tabs, value='One'):
        with ui.tab_panel('One'):
            ui.label('panel one')
    with ui.stepper().props('vertical'):
        with ui.step('First'):
            ui.label('step one')
            with ui.stepper_navigation():
                ui.button('Next')


@ui.page('/app')
def realistic() -> None:
    with ui.header():
        ui.label('App')
    with ui.left_drawer():
        ui.label('menu')
    with ui.footer():
        ui.label('foot')
    ui.input('name')
    ui.number('n', value=1)
    ui.select(['a', 'b'], value='a')
    ui.checkbox('c')
    ui.radio(['x', 'y'], value='x')
    ui.switch('s')
    ui.slider(min=0, max=10, value=5)
    ui.textarea('t')
    ui.button('go', icon='home')
    ui.toggle(['1', '2'], value='1')
    with ui.card():
        ui.label('card')
        ui.separator()
        ui.markdown('**md**')
    ui.table(columns=[{'name': 'a', 'label': 'A', 'field': 'a'}], rows=[{'a': 1}])
    with ui.tabs() as tabs:
        ui.tab('One')
    with ui.tab_panels(tabs, value='One'):
        with ui.tab_panel('One'):
            ui.label('p')
    with ui.expansion('more'):
        ui.label('inner')
    ui.linear_progress(0.5)
    ui.circular_progress(0.5)
    ui.spinner()
    ui.badge('9')
    ui.chip('chip')
    ui.avatar('home')
    ui.knob(0.3)
    ui.date()
    ui.time()
    ui.color_input('col')
    with ui.list():
        with ui.item():
            with ui.item_section():
                ui.item_label('item')
    ui.pagination(1, 5, value=1)
    ui.splitter()
    with ui.timeline():
        ui.timeline_entry('t', title='x')
    ui.tree([{'id': 'a'}])
    ui.editor()
    ui.upload()
    ui.menu()
    ui.tooltip('tip')


ui.run(port=PORT, show=False, reload=False)
