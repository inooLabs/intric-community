# MIT License

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from intric.files import audio
from intric.files.audio import AudioMimeTypes
from intric.files.file_models import File
from intric.transcription_models.infrastructure.adapters.whisper import (
    OpenAISTTModelAdapter,
)

if TYPE_CHECKING:
    from intric.files.file_repo import FileRepository
    from intric.transcription_models.domain.transcription_model import (
        TranscriptionModel,
    )


class Transcriber:
    def __init__(self, file_repo: "FileRepository"):
        self.file_repo = file_repo

    async def transcribe(self, file: File, transcription_model: "TranscriptionModel"):
        if file.blob is None or not AudioMimeTypes.has_value(file.mimetype):
            raise ValueError("File needs to be an audio file")

        # If file already has a transcription, return it
        if file.transcription:
            return file.transcription

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(file.blob)
                temp_file_path = Path(temp_file.name)

            result = await self.transcribe_from_filepath(
                filepath=temp_file_path, transcription_model=transcription_model
            )

            # Store the transcription in the file object
            file.transcription = result

            # If we have a repository, update the file in the database
            if self.file_repo:
                await self.file_repo.update(file)
        finally:
            temp_file_path.unlink()  # Clean up the temporary file

        return result

    async def transcribe_from_filepath(
        self, *, filepath: Path, transcription_model: "TranscriptionModel"
    ):
        adapter = OpenAISTTModelAdapter(model=transcription_model)

        async with audio.to_wav(filepath) as wav_file:
            return await adapter.get_text_from_file(wav_file)
