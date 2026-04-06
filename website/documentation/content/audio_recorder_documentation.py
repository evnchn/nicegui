from nicegui import ui

from . import doc


@doc.demo(ui.audio_recorder)
def main_demo() -> None:
    ui.audio_recorder(on_audio_ready=lambda e: ui.notify(f'Recorded {e.file.name} ({e.file.size()} bytes)'))


@doc.demo('Controlling the recorder', '''
    This demo shows how to start and stop recording programmatically.
''')
def control_demo() -> None:
    recorder = ui.audio_recorder(on_audio_ready=lambda e: ui.notify(f'Got {e.file.size()} bytes'))
    ui.button('Start', on_click=recorder.start)
    ui.button('Stop', on_click=recorder.stop)


@doc.demo('Save recording to file', '''
    This demo saves the recorded audio to a file on the server.
''')
def save_demo() -> None:
    from nicegui import events

    async def handle_audio(e: events.UploadEventArguments):
        await e.file.save(f'/tmp/{e.file.name}')
        ui.notify(f'Saved to /tmp/{e.file.name}')

    ui.audio_recorder(on_audio_ready=handle_audio)


doc.reference(ui.audio_recorder)
