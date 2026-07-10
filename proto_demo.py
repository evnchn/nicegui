#!/usr/bin/env python3
"""PR #5613 design comparison demo: two shapes of a "popup edit", side by side.

LEFT  = the container PRIMITIVE currently in the PR (``ui.popup_edit``):
        a dumb container; child elements bind their own values out via NiceGUI binding.

RIGHT = the AWAITABLE-SINGLETON alternative (``ui.popup_edit_awaitable``, prototype):
        ONE reusable editor, repositioned per table cell, driven as
        ``value = await popup.edit(initial, target=..., cell=...)``.

Run:  .venv/bin/python proto_demo.py
"""
from nicegui import app, ui


@ui.page('/')
def index() -> None:
    ui.dark_mode(True)
    ui.label('PR #5613 — popup_edit design comparison').classes('text-h5 q-mb-md')

    with ui.row().classes('w-full no-wrap q-col-gutter-lg'):

        # ---------------------------------------------------------------- LEFT
        with ui.column().classes('col'):
            ui.label('(a) Container PRIMITIVE — ui.popup_edit').classes('text-h6')
            ui.markdown(
                'Child `ui.input` binds its own value out. The popup is just a shell; '
                'NiceGUI data-binding does the work. Click the label to edit.'
            ).classes('text-caption')

            app.storage.client['name'] = 'NiceGUI User'
            with ui.label().bind_text_from(app.storage.client, 'name').classes('text-primary cursor-pointer'):
                with ui.popup_edit(on_show=lambda _: ui.notify('Shown!'),
                                   on_hide=lambda _: ui.notify('Hidden!')):
                    ui.input().bind_value(app.storage.client, 'name')
            ui.label().bind_text_from(app.storage.client, 'name',
                                      backward=lambda n: f'server sees: {n!r}').classes('text-caption')

        # --------------------------------------------------------------- RIGHT
        with ui.column().classes('col'):
            ui.label('(b) Awaitable SINGLETON — ui.popup_edit_awaitable').classes('text-h6')
            ui.markdown(
                'ONE editor instance for the whole table. Click a cell → '
                '`value = await popup.edit(...)` opens it *at that cell*, resolves to '
                'the new value on OK or `None` on cancel.'
            ).classes('text-caption')

            data = [['Alice', '30', 'Berlin'],
                    ['Bob', '25', 'Paris'],
                    ['Carol', '41', 'Tokyo']]
            headers = ['Name', 'Age', 'City']

            # The single, shared editor -- created once, reused for every cell.
            popup = ui.popup_edit_awaitable(
                on_submit=lambda e: ui.notify(f'submit cell {e.cell} -> {e.value!r}'))

            cell_labels: dict[tuple, ui.label] = {}

            async def edit_cell(r: int, c: int) -> None:
                new = await popup.edit(data[r][c], target=f'#cell-{r}-{c}', cell=(r, c))
                if new is not None:  # None == cancelled
                    data[r][c] = new
                    cell_labels[(r, c)].set_text(new)

            with ui.grid(columns=3).classes('gap-0 border'):
                for h in headers:
                    ui.label(h).classes('text-bold p-2 bg-primary text-white')
                for r, row in enumerate(data):
                    for c, val in enumerate(row):
                        lbl = ui.label(val).classes('p-2 border cursor-pointer hover:bg-slate-700')
                        lbl.props(f'id=cell-{r}-{c}')
                        lbl.on('click', lambda r=r, c=c: edit_cell(r, c))
                        cell_labels[(r, c)] = lbl

            ui.label('Click any cell above to edit it via the shared popup.').classes('text-caption')


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(port=8123, show=False, reload=False)
