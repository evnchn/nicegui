# Terminal Serve

Serve any terminal application in the browser using [xterm.js](https://github.com/xtermjs/xterm.js), inspired by [textual-serve](https://github.com/Textualize/textual-serve).

Unlike textual-serve, which only works with Textual apps, this example works with **any** terminal program — interactive shells, TUI apps, scripts, etc.

## Features

- Serve any command via a full xterm.js terminal in the browser
- Dark themed UI with start/restart screens
- Auto-resizing terminal with PTY size synchronization
- Each browser tab gets its own isolated subprocess
- Configurable command, title, host, and port via CLI
- Truecolor support (`TERM=xterm-256color`)
- Automatic cleanup on disconnect

## Usage

```bash
# Serve bash (default)
python main.py

# Serve a specific command
python main.py "htop"
python main.py "python3 -m textual_paint"

# Custom title and port
python main.py --title "My App" --port 9000 "my_command"
```

## Warning

This example gives each connected browser client access to run the configured command on the server.
When serving an interactive shell like bash, clients have full access to the server. Use with caution!
