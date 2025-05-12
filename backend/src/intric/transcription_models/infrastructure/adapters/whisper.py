# MIT License

from pathlib import Path

import openai
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from intric.files.audio import AudioFile
from intric.main.config import SETTINGS
from intric.main.exceptions import BadRequestException, OpenAIException
from intric.main.logging import get_logger
from intric.transcription_models.domain import TranscriptionModel

logger = get_logger(__name__)


class OpenAISTTModelAdapter:
    def __init__(self, model: TranscriptionModel):
        self.model = model
        self.client = AsyncOpenAI(api_key=SETTINGS.openai_api_key, base_url=model.base_url)

    async def get_text_from_file(self, audio_file: AudioFile):
        text = ""
        five_minutes = 60 * 5
        chunk_index = 0
        total_duration_seconds = int(audio_file.info.duration)

        async with audio_file.asplit_file(seconds=five_minutes) as files:
            total_chunks = len(files)

            for i, path in enumerate(files):
                block_text = await self._get_text_from_file(path)
                start_time = chunk_index * five_minutes

                # For the last chunk, calculate the correct end time based on total duration
                if i == total_chunks - 1:
                    end_time = total_duration_seconds
                else:
                    end_time = (chunk_index + 1) * five_minutes

                start_time_formatted = f"{start_time // 60}:{start_time % 60:02d}"
                end_time_formatted = f"{end_time // 60}:{end_time % 60:02d}"

                # Add markdown formatting with timestamp
                if chunk_index > 0:
                    text += "\n\n"
                text += f"### {start_time_formatted} - {end_time_formatted}\n\n{block_text}"
                chunk_index += 1

        return text

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(3),
        retry=retry_if_not_exception_type(BadRequestException),
        reraise=True,
    )
    async def _get_text_from_file(self, file: Path):
        try:
            transcription = await self.client.audio.transcriptions.create(
                model=self.model.name,
                file=file,
            )
        except openai.BadRequestError as e:
            logger.exception("Bad request error:")
            raise BadRequestException("Invalid input") from e
        except openai.RateLimitError as e:
            logger.exception("Rate limit error:")
            raise OpenAIException("OpenAI Ratelimit exception") from e
        except Exception as e:
            logger.exception("Unknown OpenAI exception:")
            raise OpenAIException("Unknown OpenAI exception") from e

        return transcription.text
