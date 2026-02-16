import httpx

from nicegui import events, ui
from nicegui.elements.audio_recorder import AudioRecorder
from nicegui.testing import Screen


def test_audio_recorder_renders(screen: Screen):
    @ui.page('/')
    def page():
        ui.audio_recorder()

    screen.open('/')
    assert screen.find_by_tag('button').get_attribute('title') == 'Start recording'


def test_audio_recorder_replace(screen: Screen):
    @ui.page('/')
    def page():
        with ui.row() as container:
            ui.audio_recorder()
        ui.button('Replace', on_click=container.clear)

    screen.open('/')
    assert screen.find_by_tag('button').get_attribute('title') == 'Start recording'
    screen.click('Replace')
    screen.wait(0.5)


async def test_audio_recorder_upload_route(screen: Screen):
    results: list[events.UploadEventArguments] = []
    recorder_ref: list[AudioRecorder] = []

    @ui.page('/')
    def page():
        recorder = ui.audio_recorder(on_audio_ready=results.append)
        recorder_ref.append(recorder)

    screen.open('/')

    audio_rec = recorder_ref[0]
    url = audio_rec._props['url']

    audio_data = b'\x00\x01\x02\x03' * 100
    files = {'file': ('recording.webm', audio_data, 'audio/webm')}
    async with httpx.AsyncClient(base_url=screen.url) as client:
        response = await client.post(url, files=files)
    assert response.status_code == 200
    screen.wait(0.1)
    assert len(results) == 1
    assert results[0].file.name == 'recording.webm'
    assert results[0].file.content_type == 'audio/webm'
    assert await results[0].file.read() == audio_data
