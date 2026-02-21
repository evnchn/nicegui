from nicegui import ui

from . import doc

doc.title('*NiceGUI* Architecture')
doc.metadata(difficulty='intermediate')


@doc.part('Overview')
def overview():
    ui.markdown('''
        NiceGUI follows a **backend-first** philosophy:
        all UI logic is written in Python on the server, and NiceGUI handles the web layer transparently.
        This page explains how the different layers of the framework interact at runtime.
    ''')


@doc.part('Backend-First Architecture')
def backend_first():
    ui.markdown('''
        Unlike traditional web frameworks where you write HTML, CSS, and JavaScript on the client side,
        NiceGUI lets you describe the entire interface in Python.
        The framework translates your Python element tree into a Vue 3 component tree
        and keeps both sides in sync over a persistent WebSocket connection.

        The diagram below shows the three main layers of a running NiceGUI application.
    ''')
    ui.mermaid('''
        graph TD
            subgraph Server["Python Server (FastAPI / Starlette)"]
                A[Your Python Code] --> B[NiceGUI Element Tree]
                B --> C[Outbox / Diff Engine]
            end
            subgraph Transport["Transport Layer"]
                C <-->|WebSocket messages| D[Browser WebSocket Client]
            end
            subgraph Browser["Browser (Vue 3 + Quasar)"]
                D --> E[Vue Component Tree]
                E --> F[Rendered DOM]
                F -->|User Events| D
            end
    ''')


@doc.part('Request / Response Lifecycle')
def lifecycle():
    ui.markdown('''
        When a user first visits a NiceGUI page, the following sequence occurs.
    ''')
    ui.mermaid('''
        sequenceDiagram
            participant Browser
            participant FastAPI
            participant NiceGUI
            participant YourCode

            Browser->>FastAPI: HTTP GET /your-page
            FastAPI->>NiceGUI: Route matched, create Client
            NiceGUI->>YourCode: Execute page function
            YourCode->>NiceGUI: Build element tree
            NiceGUI->>FastAPI: Return initial HTML (Jinja2 template)
            FastAPI->>Browser: HTML + JS bundle
            Browser->>FastAPI: WebSocket upgrade
            FastAPI->>NiceGUI: WebSocket connected
            NiceGUI->>Browser: Send initial element tree (JSON)
            Browser->>Browser: Mount Vue components
    ''')


@doc.part('Event Handling')
def event_handling():
    ui.markdown('''
        After the initial page load, all communication is bidirectional over the WebSocket.
        When the user interacts with the page (e.g., clicks a button), the browser emits an event message.
        NiceGUI receives this message, calls your Python event handler,
        and then sends any resulting UI updates back to the browser as a diff.
    ''')
    ui.mermaid('''
        sequenceDiagram
            participant Browser
            participant NiceGUI
            participant YourHandler

            Browser->>NiceGUI: Event message (e.g., button click)
            NiceGUI->>YourHandler: Call on_click handler
            YourHandler->>NiceGUI: Modify element properties
            NiceGUI->>Browser: Send UI update diff (JSON)
            Browser->>Browser: Patch Vue component tree
    ''')


@doc.part('Binding System')
def binding_system():
    ui.markdown('''
        The binding system connects Python model attributes to UI element properties.
        There are two types of bindings.

        **Bindable properties** (used by most built-in elements) detect write access via Python descriptors
        and immediately propagate the new value to all connected elements.
        They are zero-cost when the value does not change.

        **Active links** poll for changes in a background `refresh_loop()` that runs every 0.1 seconds.
        These are used when binding to plain Python objects, dictionaries, or custom classes.
        The polling interval can be configured via `binding_refresh_interval` in `ui.run()`.
    ''')
    ui.mermaid('''
        graph LR
            subgraph Model["Python Model"]
                P[BindableProperty / dict / object]
            end
            subgraph Binding["Binding Layer"]
                B1[Bindable Property Descriptor]
                B2[Active Link Refresh Loop]
            end
            subgraph UI["UI Elements"]
                E1[ui.input]
                E2[ui.label]
                E3[ui.slider]
            end

            P -->|write triggers| B1
            P -.->|polled every 0.1s| B2
            B1 --> E1
            B1 --> E2
            B2 --> E3
            E1 -->|user input| P
    ''')


@doc.part('Multi-User and Session Isolation')
def multi_user():
    ui.markdown('''
        NiceGUI is designed for multi-user deployments.
        Each browser connection creates an isolated `Client` object that owns its own element tree.
        Storage is available at three scopes.

        | Scope | API | Lifetime | Shared? |
        |---|---|---|---|
        | Browser tab | `app.storage.tab` | Until tab closes | No |
        | User session | `app.storage.user` | Configurable (cookie-based) | Across tabs |
        | Application | `app.storage.general` | Until server restarts | All users |

        Because all UI mutations happen on the main event loop thread,
        you do not need to worry about thread safety for UI updates.
        Use `background_tasks.create()` for long-running work to keep the event loop responsive.
    ''')


@doc.part('Further Reading')
def further_reading():
    ui.markdown('''
        - [Binding Properties](/documentation/section_binding_properties) - full binding API reference
        - [Pages & Routing](/documentation/section_pages_routing) - how `@ui.page` and `ui.sub_pages` work
        - [Configuration & Deployment](/documentation/section_configuration_deployment) - `ui.run()` options
        - [Action & Events](/documentation/section_action_events) - timers, keyboard, and async handlers
        - [Testing](/documentation/section_testing) - the `User` and `Screen` test fixtures
    ''').classes('bold-links arrow-links')
