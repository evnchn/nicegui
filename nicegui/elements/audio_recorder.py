from typing import cast

from fastapi import Request
from starlette.datastructures import UploadFile
from typing_extensions import Self

from ..element import Element
from ..events import Handler, UploadEventArguments, handle_event
from ..nicegui import app
from .upload_files import create_file_upload


class AudioRecorder(Element, component='audio_recorder.js'):

    def __init__(self, *,
                 on_audio_ready: Handler[UploadEventArguments] | None = None,
                 mime_type: str | None = None,
                 ) -> None:
        """Audio Recorder

        Provides a button to record audio from the user's microphone using the browser's
        `MediaRecorder API <https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder>`_.

        When the recording is stopped, the audio data is uploaded to the server and the
        ``on_audio_ready`` callback is invoked with an ``UploadEventArguments`` containing
        the recorded audio as a ``FileUpload`` object.

        Note: The user's browser will ask for microphone permission when recording starts.

        :param on_audio_ready: callback to execute when a recording is complete and audio data is available
        :param mime_type: preferred MIME type for the recording (e.g. ``"audio/webm"``, ``"audio/mp4"``); \
            falls back to the browser's default if unsupported (default: ``None``)
        """
        super().__init__()
        self._props['url'] = f'/_nicegui/client/{self.client.id}/audio_recorder/{self.id}'
        self._props.set_optional('mime-type', mime_type)

        self._audio_ready_handlers: list[Handler[UploadEventArguments]] = []
        if on_audio_ready:
            self._audio_ready_handlers.append(on_audio_ready)

        @app.post(self._props['url'])
        async def upload_route(request: Request) -> dict[str, str]:
            async with request.form() as form:
                files = [await create_file_upload(cast(UploadFile, data)) for data in form.values()]
            for file in files:
                for handler in self._audio_ready_handlers:
                    handle_event(handler, UploadEventArguments(sender=self, client=self.client, file=file))
            return {'status': 'ok'}

    def on_audio_ready(self, callback: Handler[UploadEventArguments]) -> Self:
        """Add a callback to be invoked when audio recording data is ready.

        :param callback: callback to execute with an ``UploadEventArguments`` containing the recorded audio
        """
        self._audio_ready_handlers.append(callback)
        return self

    def start(self) -> None:
        """Start recording audio from the microphone."""
        self.run_method('start')

    def stop(self) -> None:
        """Stop recording audio."""
        self.run_method('stop')

    def _handle_delete(self) -> None:
        app.remove_route(self._props['url'])
        super()._handle_delete()
