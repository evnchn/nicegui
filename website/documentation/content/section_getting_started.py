from nicegui import ui

from . import (
    architecture_documentation,
    doc,
)

doc.title('*Getting* Started')
doc.metadata(difficulty='beginner')


@doc.demo('Installation', '''
    Install NiceGUI from PyPI using pip.
    Python 3.10 or newer is required.
''')
def installation_demo():
    # pip install nicegui
    ui.label('NiceGUI installed!')


@doc.demo('Hello World', '''
    The simplest NiceGUI application creates a label and starts the server.
    Save the following code as `main.py` and run it with `python main.py`.
    NiceGUI will open your browser automatically at `http://localhost:8080`.
''')
def hello_world_demo():
    # from nicegui import ui
    #
    # ui.label('Hello, NiceGUI!')
    #
    # ui.run()
    ui.label('Hello, NiceGUI!')


@doc.demo('Adding Interactivity', '''
    Attach an `on_click` handler to a button to respond to user actions.
    The handler is a plain Python function or coroutine.
''')
def interactivity_demo():
    def greet():
        ui.notify('Hello from Python!')

    ui.button('Greet', on_click=greet)


@doc.demo('Reactive Data Binding', '''
    Bind a UI element's value directly to a Python variable or model attribute.
    The interface updates automatically whenever the model changes.
''')
def binding_demo():
    class Model:
        text = 'NiceGUI'

    model = Model()
    ui.input('Name').bind_value(model, 'text')
    ui.label().bind_text_from(model, 'text', backward=lambda t: f'Hello, {t}!')


@doc.demo('Layout with Context Managers', '''
    Use Python's `with` statement to nest elements inside layout containers.
    This mirrors the visual hierarchy of the resulting UI.
''')
def layout_demo():
    with ui.card():
        ui.label('Card title').classes('text-lg font-bold')
        with ui.row():
            ui.button('OK')
            ui.button('Cancel')


doc.intro(architecture_documentation)

doc.text('Learning Path', '''
    After completing the basics above, follow this recommended learning path.

    1. **Core UI Elements** - explore [Text Elements](/documentation/section_text_elements),
       [Controls](/documentation/section_controls), and
       [Audiovisual Elements](/documentation/section_audiovisual_elements).
    2. **Layout & Styling** - learn [Page Layout](/documentation/section_page_layout) and
       [Styling & Appearance](/documentation/section_styling_appearance).
    3. **Reactivity** - understand [Binding Properties](/documentation/section_binding_properties) and
       [Action & Events](/documentation/section_action_events).
    4. **Multi-Page Apps** - read [Pages & Routing](/documentation/section_pages_routing).
    5. **Production** - study [Configuration & Deployment](/documentation/section_configuration_deployment)
       and [Security](/documentation/section_security).
    6. **Quality** - write tests with the [Testing](/documentation/section_testing) guide.
''')
