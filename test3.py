from pathlib import Path

from nicegui import app, ui

app.add_static_file(local_file=Path(__file__).parent / 'basecoat.quasar.css', url_path='/basecoat.quasar.css')

ui.add_head_html('''<link rel="stylesheet" href="/basecoat.quasar.css">
<style>
@layer theme {
    body {
        --primary: var(--q-primary);
    }
}
</style>''', shared=True)

ui.link.default_classes('rounded-md')
ui.input.default_props('borderless dense input-class="input-text"')
ui.number.default_props('borderless dense input-class="input-text"')
ui.textarea.default_props('borderless dense input-class="textarea"')
ui.color_input.default_props('borderless dense input-class="input-text"')
ui.date_input.default_props('borderless dense input-class="input-text"')
ui.time_input.default_props('borderless dense input-class="input-text"')
ui.select.default_props('borderless dense').default_classes('input-text *:-mt-1.5')


@ui.page('/')
def main_page():
    ui.colors(primary='black')
    ui.button('Click me', on_click=lambda: ui.notify('Button clicked!'))

    with ui.card():
        ui.label('Normal card')

    ui.checkbox('Check me (normal)', on_change=lambda e: ui.notify(f'Normal checkbox: {e.value}'))

    ui.input(on_change=lambda e: ui.notify(f'Input changed to: {e.value}'), placeholder='MyPlaceholder')
    ui.number(on_change=lambda e: ui.notify(f'Number changed to: {e.value}'), placeholder='MyPlaceholder')
    ui.textarea(on_change=lambda e: ui.notify(f'Textarea changed to: {e.value}'), placeholder='MyPlaceholder')
    ui.select(options=['Option 1', 'Option 2', 'Option 3'], on_change=lambda e: ui.notify(
        f'Select changed to: {e.value}'))

    ui.badge('Badge')
    ui.badge('Badge')

    ui.switch('Toggle me (normal)', on_change=lambda e: ui.notify(f'Normal toggle: {e.value}'))

    with ui.button_group():
        ui.button('One', on_click=lambda: ui.notify('You clicked Button 1!'))
        ui.button('Two', on_click=lambda: ui.notify('You clicked Button 2!'))
        ui.button('Three', on_click=lambda: ui.notify('You clicked Button 3!'))

    ui.radio([1, 2, 3], value=1).props('inline')

    dark = ui.dark_mode()
    ui.switch('Dark mode').bind_value(dark)


ui.run()
