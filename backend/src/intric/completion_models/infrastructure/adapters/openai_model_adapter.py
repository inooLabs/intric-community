import base64
import json

from openai import AsyncOpenAI

from intric.ai_models.completion_models.completion_model import (
    CompletionModel,
    Context,
    ModelKwargs,
)
from intric.completion_models.infrastructure import get_response_open_ai
from intric.completion_models.infrastructure.adapters.base_adapter import (
    CompletionModelAdapter,
)
from intric.files.file_models import File
from intric.logging.logging import LoggingDetails
from intric.main.config import get_settings
from intric.main.logging import get_logger

logger = get_logger(__name__)


TOKENS_RESERVED_FOR_COMPLETION = 1000


class OpenAIModelAdapter(CompletionModelAdapter):
    def __init__(
        self,
        model: CompletionModel,
        client: AsyncOpenAI = AsyncOpenAI(api_key=get_settings().openai_api_key),
    ):
        self.model = model
        self.client = client
        self.extra_headers = None

    def _get_kwargs(self, kwargs: ModelKwargs | None):
        if kwargs is None:
            return {}

        return kwargs.model_dump(exclude_none=True)

    def get_token_limit_of_model(self):
        return self.model.token_limit - TOKENS_RESERVED_FOR_COMPLETION

    def get_logging_details(self, context: Context, model_kwargs: ModelKwargs):
        query = self.create_query_from_context(context=context)
        return LoggingDetails(
            json_body=json.dumps(query), model_kwargs=self._get_kwargs(model_kwargs)
        )

    def _build_image(self, file: File):
        image_data = base64.b64encode(file.blob).decode("utf-8")

        return {
            "type": "image_url",
            "image_url": {"url": f"data:{file.mimetype};base64,{image_data}"},
        }

    def _build_content(
        self,
        input: str,
        images: list[File],
    ):
        content = (
            [
                {
                    "type": "text",
                    "text": input,
                }
            ]
            if input
            else []
        )

        for image in images:
            content.append(self._build_image(image))

        return content

    def _build_tools_from_context(self, context: Context):
        if not context.function_definitions:
            return []

        if not self.model.vision:
            return []

        return [
            {
                "type": "function",
                "function": {
                    "name": function_definition.name,
                    "description": function_definition.description,
                    "parameters": function_definition.schema,
                    "strict": True,
                },
            }
            for function_definition in context.function_definitions
        ]

    def create_query_from_context(self, context: Context):
        system_message = [{"role": "system", "content": context.prompt}]

        previous_messages = [
            message
            for question in context.messages
            for message in [
                {
                    "role": "user",
                    "content": self._build_content(
                        input=question.question,
                        images=question.images + question.generated_images,
                    ),
                },
                {
                    "role": "assistant",
                    "content": question.answer,
                },
            ]
        ]
        question = [
            {
                "role": "user",
                "content": self._build_content(
                    input=context.input,
                    images=context.images,
                ),
            }
        ]

        return system_message + previous_messages + question

    async def get_response(
        self,
        context: Context,
        model_kwargs: ModelKwargs | None = None,
    ):
        query = self.create_query_from_context(context=context)
        return await get_response_open_ai.get_response(
            client=self.client,
            model_name=self.model.name,
            messages=query,
            model_kwargs=self._get_kwargs(model_kwargs),
            extra_headers=self.extra_headers,
        )

    def get_response_streaming(
        self,
        context: Context,
        model_kwargs: ModelKwargs | None = None,
    ):
        query = self.create_query_from_context(context=context)
        tools = self._build_tools_from_context(context=context)
        return get_response_open_ai.get_response_streaming(
            client=self.client,
            model_name=self.model.name,
            messages=query,
            model_kwargs=self._get_kwargs(model_kwargs),
            tools=tools,
            extra_headers=self.extra_headers,
        )
