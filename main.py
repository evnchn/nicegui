#!/usr/bin/env python3
import os
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse, Response

from nicegui import app, core, ui
from nicegui.page_arguments import RouteMatch
from website import design as d
from website import documentation, examples_page, fly, header, imprint_privacy, main_page, rate_limits, svg
from website.components import footer_section
from website.documentation.intersection_observer import IntersectionObserver as intersection_observer

app.add_static_file(local_file=Path(__file__).parent / 'basecoat.quasar.css', url_path='/basecoat.quasar.css')

ui.add_head_html('''<link rel="stylesheet" href="/basecoat.quasar.css">
<style>
@layer theme {
    body {
        --primary: var(--q-primary);
    }
  body {
    --background: oklch(0.85 0 0);
    --foreground: oklch(0.24 0 0);
    --card: oklch(0.76 0 0);
    --card-foreground: oklch(0.24 0 0);
    --popover: oklch(0.76 0 0);
    --popover-foreground: oklch(0.24 0 0);
    --primary: oklch(0.50 0.19 27.48);
    --primary-foreground: oklch(1.00 0 0);
    --secondary: oklch(0.50 0.09 126.19);
    --secondary-foreground: oklch(1.00 0 0);
    --muted: oklch(0.78 0 0);
    --muted-foreground: oklch(0.41 0 0);
    --accent: oklch(0.59 0.10 245.74);
    --accent-foreground: oklch(1.00 0 0);
    --destructive: oklch(0.71 0.20 46.46);
    --destructive-foreground: oklch(0 0 0);
    --border: oklch(0.43 0 0);
    --input: oklch(0.43 0 0);
    --ring: oklch(0.50 0.19 27.48);
    --chart-1: oklch(0.50 0.19 27.48);
    --chart-2: oklch(0.50 0.09 126.19);
    --chart-3: oklch(0.59 0.10 245.74);
    --chart-4: oklch(0.71 0.20 46.46);
    --chart-5: oklch(0.57 0.04 40.43);
    --sidebar: oklch(0.76 0 0);
    --sidebar-foreground: oklch(0.24 0 0);
    --sidebar-primary: oklch(0.50 0.19 27.48);
    --sidebar-primary-foreground: oklch(1.00 0 0);
    --sidebar-accent: oklch(0.59 0.10 245.74);
    --sidebar-accent-foreground: oklch(1.00 0 0);
    --sidebar-border: oklch(0.43 0 0);
    --sidebar-ring: oklch(0.50 0.19 27.48);
    --font-sans: "Oxanium", sans-serif;
    --font-serif: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
    --font-mono: "Source Code Pro", monospace;
    --radius: 0px;
    --shadow-2xs: 0px 2px 4px 0px hsl(0 0% 0% / 0.20);
    --shadow-xs: 0px 99px 99px 0px hsl(0 0% 0% / 0.20);
    --shadow-sm: 0px 2px 4px 0px hsl(0 0% 0% / 0.40), 0px 1px 2px -1px hsl(0 0% 0% / 0.40);
    --shadow: 0px 2px 4px 0px hsl(0 0% 0% / 0.40), 0px 1px 2px -1px hsl(0 0% 0% / 0.40);
    --shadow-md: 0px 2px 4px 0px hsl(0 0% 0% / 0.40), 0px 2px 4px -1px hsl(0 0% 0% / 0.40);
    --shadow-lg: 0px 2px 4px 0px hsl(0 0% 0% / 0.40), 0px 4px 6px -1px hsl(0 0% 0% / 0.40);
    --shadow-xl: 0px 2px 4px 0px hsl(0 0% 0% / 0.40), 0px 8px 10px -1px hsl(0 0% 0% / 0.40);
    --shadow-2xl: 0px 2px 4px 0px hsl(0 0% 0% / 1.00);
  }

  body.body--dark {
    --background: oklch(0.22 0 0);
    --foreground: oklch(0.91 0 0);
    --card: oklch(0.29 0 0);
    --card-foreground: oklch(0.91 0 0);
    --popover: oklch(0.29 0 0);
    --popover-foreground: oklch(0.91 0 0);
    --primary: oklch(0.61 0.21 27.03);
    --primary-foreground: oklch(1.00 0 0);
    --secondary: oklch(0.64 0.15 133.01);
    --secondary-foreground: oklch(0 0 0);
    --muted: oklch(0.26 0 0);
    --muted-foreground: oklch(0.71 0 0);
    --accent: oklch(0.75 0.12 244.75);
    --accent-foreground: oklch(0 0 0);
    --destructive: oklch(0.78 0.17 68.09);
    --destructive-foreground: oklch(0 0 0);
    --border: oklch(0.41 0 0);
    --input: oklch(0.41 0 0);
    --ring: oklch(0.61 0.21 27.03);
    --chart-1: oklch(0.61 0.21 27.03);
    --chart-2: oklch(0.64 0.15 133.01);
    --chart-3: oklch(0.75 0.12 244.75);
    --chart-4: oklch(0.78 0.17 68.09);
    --chart-5: oklch(0.65 0.03 40.80);
    --sidebar: oklch(0.19 0 0);
    --sidebar-foreground: oklch(0.91 0 0);
    --sidebar-primary: oklch(0.61 0.21 27.03);
    --sidebar-primary-foreground: oklch(1.00 0 0);
    --sidebar-accent: oklch(0.75 0.12 244.75);
    --sidebar-accent-foreground: oklch(0 0 0);
    --sidebar-border: oklch(0.41 0 0);
    --sidebar-ring: oklch(0.61 0.21 27.03);
    --font-sans: "Oxanium", sans-serif;
    --font-serif: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
    --font-mono: "Source Code Pro", monospace;
    --radius: 0px;
    --shadow-2xs: 0px 2px 5px 0px hsl(0 0% 0% / 0.30);
    --shadow-xs: 0px 2px 5px 0px hsl(0 0% 0% / 0.30);
    --shadow-sm: 0px 2px 5px 0px hsl(0 0% 0% / 0.60), 0px 1px 2px -1px hsl(0 0% 0% / 0.60);
    --shadow: 0px 2px 5px 0px hsl(0 0% 0% / 0.60), 0px 1px 2px -1px hsl(0 0% 0% / 0.60);
    --shadow-md: 0px 2px 5px 0px hsl(0 0% 0% / 0.60), 0px 2px 4px -1px hsl(0 0% 0% / 0.60);
    --shadow-lg: 0px 2px 5px 0px hsl(0 0% 0% / 0.60), 0px 4px 6px -1px hsl(0 0% 0% / 0.60);
    --shadow-xl: 0px 2px 5px 0px hsl(0 0% 0% / 0.60), 0px 8px 10px -1px hsl(0 0% 0% / 0.60);
    --shadow-2xl: 0px 2px 5px 0px hsl(0 0% 0% / 1.50);
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


@app.add_middleware
class DocsSetCacheControlMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if request.url.path.startswith('/fonts/') or request.url.path.startswith('/static/'):
            response.headers['Cache-Control'] = core.app.config.cache_control_directives
        elif request.url.path.startswith('/examples/images/'):
            response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
        return response


# session middleware is required for demo in documentation
app.add_middleware(SessionMiddleware, secret_key=os.environ.get('NICEGUI_SECRET_KEY', ''))
rate_limits.setup()

on_fly = fly.setup()

app.add_static_files('/favicon', str(Path(__file__).parent / 'website' / 'favicon'))
app.add_static_files('/fonts', str(Path(__file__).parent / 'website' / 'fonts'))
app.add_static_files('/static', str(Path(__file__).parent / 'website' / 'static'))
app.add_static_file(local_file=svg.PATH / 'logo.png', url_path='/logo.png')
app.add_static_file(local_file=svg.PATH / 'logo_square.png', url_path='/logo_square.png')

documentation.build_search_index()
documentation.build_tree()


@app.get('/llms.md')
@app.get('/llms.txt')
def _get_llms() -> FileResponse:
    return FileResponse(Path(__file__).parent / 'nicegui' / 'llms.md', media_type='text/markdown; charset=utf-8')


@app.post('/dark_mode')
async def _post_dark_mode(request: Request) -> None:
    app.storage.browser['dark_mode'] = (await request.json()).get('value')


class custom_sub_pages(ui.sub_pages):
    def _render_page(self, match: RouteMatch) -> bool:
        if match.path == '/' and match.remaining_path:
            return False
        return super()._render_page(match)


@ui.page('/')
@ui.page('/examples')
@ui.page('/documentation')
@ui.page('/documentation/{path:path}')
@ui.page('/imprint_privacy')
def _main_page() -> None:
    ui.context.client.content.classes('p-0 gap-0')

    header.add_head_html()

    with ui.left_drawer().classes(f'column no-wrap gap-1 {d.BG_FOOTER} {d.BORDER_R} p-8') as menu:
        tree = ui.tree([], label_key='title', on_select=lambda e: ui.navigate.to(f'/documentation/{e.value}')) \
            .classes(r'w-full [&_.q-tree\_\_children]:pl-4') \
            .props('accordion no-connectors no-selection-unset icon=chevron_right color=primary')
        tree.visible = False
        spinner = ui.image('/static/loading.gif').classes('w-8 h-8 m-auto').props('no-spinner no-transition')
        d.override_markdown(spinner, '')

        @intersection_observer
        def update_tree() -> None:
            tree.props['nodes'] = documentation.tree.nodes
            tree.visible = True
            spinner.delete()
    menu_button = header.add_header(menu)

    window_state = {'is_desktop': None}
    ui.on('is_desktop', lambda v: window_state.update(is_desktop=v.args))
    ui.add_head_html('''
        <script>
            const mediaQuery = window.matchMedia('(min-width: 1024px)');
            mediaQuery.addEventListener('change', e => emitEvent('is_desktop', e.matches));
            window.addEventListener('load', () => emitEvent('is_desktop', mediaQuery.matches));
        </script>
    ''')

    main_content = custom_sub_pages({
        '/': main_page.create,
        '/examples': examples_page.create,
        '/documentation': lambda: documentation.render_page(documentation.registry['']),
        '/documentation/{name}': lambda name: _documentation_detail_page(name, tree),
        '/imprint_privacy': imprint_privacy.create,
    }, show_404=False).classes('w-full')
    ui.skip_link(target=main_content)

    footer_section.create()

    def _update_menu(path: str):
        if path.startswith('/documentation/'):
            menu_button.visible = True
            if window_state['is_desktop'] is not None:
                menu.value = window_state['is_desktop']
        else:
            menu_button.visible = False
            menu.value = False
    ui.context.client.sub_pages_router.on_path_changed(_update_menu)
    _update_menu(ui.context.client.sub_pages_router.current_path)


def _documentation_detail_page(name: str, tree: ui.tree) -> None:
    tree.props.update(expanded=documentation.tree.ancestors(name))
    tree.update()
    if name in documentation.registry:
        documentation.render_page(documentation.registry[name])
    elif name in documentation.redirects:
        ui.navigate.to('/documentation/' + documentation.redirects[name])
    else:
        ui.status_code(404)
        with ui.column().classes('w-full min-h-[50vh] items-center justify-center text-center p-16'):
            ui.label(f'Documentation for "{name}" could not be found.')


@app.get('/status')
def _status():
    return 'Ok'


# do not reload on fly.io (see https://github.com/zauberzeug/nicegui/discussions/1720#discussioncomment-7288741)
ui.run(uvicorn_reload_includes='*.py, *.css, *.html', reload=not on_fly, reconnect_timeout=10.0, markdown=True)
