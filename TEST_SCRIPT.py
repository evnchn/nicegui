"""Eager tab panels demo: AG Grid is accessible even before visiting its tab."""
from nicegui import ui


@ui.page('/')
async def main():
    ui.label('Eager tab panels').classes('text-h5')

    with ui.tabs() as tabs:
        ui.tab('One')
        ui.tab('Two')
        ui.tab('Three')

    with ui.tab_panels(tabs, value='One', eager=True):
        with ui.tab_panel('One'):
            ui.label('This is the first panel.')
        with ui.tab_panel('Two'):
            grid = ui.aggrid({
                'columnDefs': [{'field': 'name'}, {'field': 'age'}],
                'rowData': [{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}],
            })
        with ui.tab_panel('Three'):
            ui.label('Third panel content')

    async def check():
        found = await ui.run_javascript(f'!!getElement({grid.id})')
        ui.notify(f'AG Grid mounted (without visiting tab): {found}')

    await ui.context.client.connected()
    await check()


ui.run()
