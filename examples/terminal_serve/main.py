#!/usr/bin/env python3
"""Serve any terminal application in the browser via xterm.js.

A NiceGUI-based alternative to textual-serve that works with any terminal program,
not just Textual apps. Each browser tab gets its own isolated subprocess.

WARNING: This gives clients access to run the configured command on the server. Use with caution!

Usage:
    python main.py                                # serves bash
    python main.py "htop"                         # serves htop
    python main.py "python3 -m textual_paint"     # serves a Textual app
    python main.py --title "My App" "my_command"  # custom browser title
"""

import argparse
import asyncio
import fcntl
import os
import pty
import shlex
import signal
import struct
import termios

from nicegui import background_tasks, core, events, ui

ACCENT = '#5e0ba7'
CARD_BG = '#1a2c34'
TERMINAL_BG = '#0c181f'
TERMINAL_THEME = {
    'background': TERMINAL_BG,
    'foreground': '#d4d4d4',
    'cursor': '#aeafad',
    'cursorAccent': TERMINAL_BG,
    'selectionBackground': '#264f78',
    'black': '#1e1e1e',
    'red': '#f44747',
    'green': '#6a9955',
    'yellow': '#d7ba7d',
    'blue': '#569cd6',
    'magenta': '#c586c0',
    'cyan': '#4ec9b0',
    'white': '#d4d4d4',
    'brightBlack': '#808080',
    'brightRed': '#f44747',
    'brightGreen': '#6a9955',
    'brightYellow': '#d7ba7d',
    'brightBlue': '#569cd6',
    'brightMagenta': '#c586c0',
    'brightCyan': '#4ec9b0',
    'brightWhite': '#e8e8e8',
}
PAGE_STYLE = f'''
    <style>
        body {{ margin: 0; overflow: hidden; background: {TERMINAL_BG}; }}
        .nicegui-content {{ padding: 0 !important; }}
        .q-page {{ min-height: 0 !important; }}
    </style>
'''
CARD_STYLE = f'background: {CARD_BG}; border-radius: 16px; min-width: 320px;'
BUTTON_STYLE = f'background: {ACCENT} !important; color: white; border-radius: 8px; font-size: 1.1rem;'


def set_pty_size(fd: int, cols: int, rows: int) -> None:
    """Resize the PTY to match terminal dimensions."""
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Serve a terminal application in the browser')
    parser.add_argument('command', nargs='?', default='/bin/bash', help='command to run (default: /bin/bash)')
    parser.add_argument('--title', default=None, help='title shown in the browser (default: command name)')
    parser.add_argument('--host', default='0.0.0.0', help='host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='port to listen on (default: 8080)')
    return parser.parse_args()


args = parse_args()
TITLE = args.title or os.path.basename(shlex.split(args.command)[0])


@ui.page('/')
def terminal_page():
    ui.add_head_html(PAGE_STYLE)

    pty_state: dict = {'fd': None, 'pid': None, 'reader_active': False}

    # --- Start screen ---
    start_screen = ui.element('div').classes('w-screen h-screen flex items-center justify-center')
    with start_screen:
        with ui.card().classes('text-center q-pa-xl').style(CARD_STYLE):
            ui.label(TITLE).classes('text-h4 text-white q-mb-sm')
            ui.label('Terminal served via NiceGUI').classes('text-grey-6 q-mb-lg')
            ui.button('Start', on_click=lambda: start_session()).classes('q-px-xl q-py-sm').style(BUTTON_STYLE)

    # --- End screen ---
    end_screen = ui.element('div').classes('w-screen h-screen flex items-center justify-center').style('display: none')
    with end_screen:
        with ui.card().classes('text-center q-pa-xl').style(CARD_STYLE):
            ui.label('Session Ended').classes('text-h4 text-white q-mb-sm')
            ui.label('The terminal process has exited.').classes('text-grey-6 q-mb-lg')
            ui.button('Restart', on_click=lambda: start_session()).classes('q-px-xl q-py-sm').style(BUTTON_STYLE)

    # --- Terminal ---
    term_container = ui.element('div').classes('w-screen h-screen').style('display: none')
    with term_container:
        terminal = ui.xterm(
            {
                'theme': TERMINAL_THEME,
                'fontFamily': '"Roboto Mono", "Cascadia Code", "Fira Code", monospace',
                'fontSize': 16,
                'cursorBlink': True,
                'cursorStyle': 'block',
                'scrollback': 10000,
                'convertEol': False,
            }
        ).classes('w-full h-full')
        ui.element('q-resize-observer').on('resize', terminal.fit)

    # --- PTY resize / spawn ---
    terminal.on('resize', lambda e: _on_terminal_resize(e.args['cols'], e.args['rows']))

    def _on_terminal_resize(cols: int, rows: int) -> None:
        if pty_state.get('pending_spawn'):
            del pty_state['pending_spawn']
            _spawn_pty(cols, rows)
        elif pty_state['fd'] is not None:
            try:
                set_pty_size(pty_state['fd'], cols, rows)
            except OSError:
                pass

    # --- Session lifecycle ---
    def _cleanup() -> None:
        if pty_state['reader_active'] and pty_state['fd'] is not None:
            try:
                core.loop.remove_reader(pty_state['fd'])
            except Exception:
                pass
            pty_state['reader_active'] = False
        if pty_state['fd'] is not None:
            try:
                os.close(pty_state['fd'])
            except OSError:
                pass
            pty_state['fd'] = None
        if pty_state['pid'] is not None:
            try:
                os.kill(pty_state['pid'], signal.SIGTERM)
            except OSError:
                pass
            try:
                os.waitpid(pty_state['pid'], os.WNOHANG)
            except (OSError, ChildProcessError):
                pass
            pty_state['pid'] = None

    def start_session() -> None:
        _cleanup()
        start_screen.style('display: none')
        end_screen.style('display: none')
        term_container.style('display: block')
        terminal.run_method('clear')
        pty_state['pending_spawn'] = True  # spawn after terminal.fit() triggers resize

    def _spawn_pty(cols: int, rows: int) -> None:
        pid, fd = pty.fork()
        if pid == pty.CHILD:
            os.environ['TERM'] = 'xterm-256color'
            os.environ['COLORTERM'] = 'truecolor'
            os.environ['COLUMNS'] = str(cols)
            os.environ['LINES'] = str(rows)
            os.execv('/bin/sh', ['/bin/sh', '-c', args.command])

        set_pty_size(fd, cols, rows)
        pty_state.update(pid=pid, fd=fd, reader_active=True)

        def _read_pty() -> None:
            try:
                data = os.read(fd, 4096)
            except OSError:
                data = b''
            if data:
                terminal.write(data)
            else:
                _on_process_exit()

        core.loop.add_reader(fd, _read_pty)

        async def _wait_for_exit() -> None:
            """Poll for child exit so we can show the end screen promptly."""
            while pty_state['pid'] == pid:
                try:
                    wpid, _ = os.waitpid(pid, os.WNOHANG)
                    if wpid != 0:
                        await asyncio.sleep(0.1)  # let final output flush
                        _on_process_exit()
                        return
                except ChildProcessError:
                    _on_process_exit()
                    return
                await asyncio.sleep(0.5)

        background_tasks.create(_wait_for_exit(), name='wait_for_exit')

    def _on_process_exit() -> None:
        if pty_state['pid'] is None:
            return  # already handled
        _cleanup()
        term_container.style('display: none')
        end_screen.style('display: flex')

    # --- Terminal input ---
    @terminal.on_data
    def _on_input(e: events.XtermDataEventArguments) -> None:
        if pty_state['fd'] is not None:
            try:
                os.write(pty_state['fd'], e.data.encode('utf-8'))
            except OSError:
                pass

    # --- Client disconnect cleanup ---
    @ui.context.client.on_delete
    def _on_disconnect() -> None:
        _cleanup()


ui.run(
    title=TITLE,
    host=args.host,
    port=args.port,
    dark=True,
    reload=False,
)
