import re
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from intric.ai_models.ai_models_service import AIModelsService
from intric.ai_models.completion_models.completion_model import ModelKwargs
from intric.ai_models.completion_models.context_builder import count_tokens
from intric.assistants.api.assistant_models import AssistantResponse
from intric.assistants.assistant import Assistant
from intric.assistants.assistant_factory import AssistantFactory
from intric.assistants.assistant_repo import AssistantRepository
from intric.authentication.auth_service import AuthService
from intric.files.file_service import FileService
from intric.groups.group_service import GroupService
from intric.main.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)
from intric.main.models import ModelId
from intric.prompts.api.prompt_models import PromptCreate
from intric.prompts.prompt import Prompt
from intric.prompts.prompt_service import PromptService
from intric.questions.question import UseTools
from intric.roles.permissions import (
    Permission,
    validate_permission,
    validate_permissions,
)
from intric.services.service_repo import ServiceRepository
from intric.spaces.api.space_models import WizardType
from intric.spaces.space_service import SpaceService
from intric.templates.assistant_template.assistant_template_service import (
    AssistantTemplateService,
)
from intric.users.user import UserInDB
from intric.websites.website_service import WebsiteService
from intric.workflows.step_repo import StepRepository

if TYPE_CHECKING:
    from intric.actors import ActorManager
    from intric.ai_models.completion_models.completion_model import (
        CompletionModel,
        CompletionModelResponse,
    )
    from intric.files.file_models import File
    from intric.services.service import DatastoreResult
    from intric.sessions.session import SessionInDB
    from intric.sessions.session_service import SessionService
    from intric.spaces.api.space_models import TemplateCreate
    from intric.spaces.space import Space

AT_TAG_PATTERN = r"<intric-at-tag: @[^>]+>"


def clean_intric_tag(input_string: str):
    return re.sub(AT_TAG_PATTERN, '', input_string)


class AssistantService:
    def __init__(
        self,
        repo: AssistantRepository,
        user: UserInDB,
        auth_service: AuthService,
        service_repo: ServiceRepository,
        step_repo: StepRepository,
        ai_models_service: AIModelsService,
        group_service: GroupService,
        website_service: WebsiteService,
        space_service: SpaceService,
        factory: AssistantFactory,
        prompt_service: PromptService,
        file_service: FileService,
        assistant_template_service: AssistantTemplateService,
        session_service: "SessionService",
        actor_manager: "ActorManager",
    ):
        self.repo = repo
        self.factory = factory
        self.user = user
        self.auth_service = auth_service
        self.service_repo = service_repo
        self.step_repo = step_repo
        self.ai_models_service = ai_models_service
        self.website_service = website_service
        self.group_service = group_service
        self.space_service = space_service
        self.prompt_service = prompt_service
        self.file_service = file_service
        self.assistant_template_service = assistant_template_service
        self.session_service = session_service
        self.actor_manager = actor_manager

        self._space = None

    async def _get_space(self, space_id: UUID):
        if self._space is not None:
            return self._space

        self._space = await self.space_service.get_space(space_id)

        return self._space

    def _get_actor(self, space: "Space"):
        return self.actor_manager.get_space_actor_from_space(space)

    def validate_space_assistant(self, space: "Space", assistant: Assistant):
        # validate completion model
        if assistant.completion_model is not None:
            if not space.is_completion_model_in_space(assistant.completion_model.id):
                raise BadRequestException("Completion model is not in space.")

        # validate groups
        for group in assistant.groups:
            if not space.is_group_in_space(group.id):
                raise BadRequestException("Group is not in space.")

        # validate websites
        for website in assistant.websites:
            if not space.is_website_in_space(website.id):
                raise BadRequestException("Website is not in space.")

    @validate_permissions(Permission.ASSISTANTS)
    async def create_assistant(
        self,
        name: str,
        prompt: PromptCreate,
        completion_model_id: UUID,
        space_id: UUID,
        completion_model_kwargs: ModelKwargs = ModelKwargs(),
        logging_enabled: bool = False,
        groups: list[UUID] = [],
        websites: list[UUID] = [],
    ):
        if logging_enabled:
            validate_permission(self.user, Permission.ADMIN)

        space = await self._get_space(space_id=space_id)
        actor = self._get_actor(space=space)

        if not actor.can_create_assistants():
            raise UnauthorizedException(
                "User does not have permission to create assistants in this space"
            )

        assistant = self.factory.create_assistant(
            name=name,
            space_id=space_id,
            completion_model_kwargs=completion_model_kwargs,
            logging_enabled=logging_enabled,
            user=self.user,
        )

        # completion model
        completion_model = await self.ai_models_service.get_completion_model(
            completion_model_id
        )
        assistant.completion_model = completion_model

        # groups
        if groups:
            groups = await self.group_service.get_groups_by_ids(groups)
            assistant.groups = groups

        # websites
        if websites:
            websites = await self.website_service.get_websites_by_ids(websites)
            assistant.websites = websites

        # prompt
        if prompt:
            prompt = await self.prompt_service.create_prompt(prompt.text)
            assistant.prompt = prompt

        assistant_in_db = await self.repo.add(assistant)

        return assistant_in_db

    async def create_space_assistant(
        self,
        name: str,
        space_id: UUID,
        template_data: Optional["TemplateCreate"] = None,
    ) -> Assistant:
        space = await self._get_space(space_id=space_id)
        actor = self._get_actor(space=space)

        if not actor.can_create_assistants():
            raise UnauthorizedException(
                "User does not have permission to create assistants in this space"
            )

        completion_model = await self.get_completion_model(space=space)

        if not template_data:
            assistant = self.factory.create_assistant(
                name=name,
                user=self.user,
                space_id=space_id,
                completion_model=completion_model,
            )

            return await self.repo.add(assistant)

        return await self._create_from_template(
            space=space,
            template_data=template_data,
            completion_model=completion_model,
            name=name,
        )

    async def _create_from_template(
        self,
        space: "Space",
        template_data: "TemplateCreate",
        completion_model: "CompletionModel",
        name: str | None = None,
    ):
        template = await self.assistant_template_service.get_assistant_template(
            assistant_template_id=template_data.id
        )

        # Validate incoming data
        template.validate_assistant_wizard_data(template_data=template_data)

        attachments = await self.file_service.get_file_infos(
            file_ids=template_data.get_ids_by_type(wizard_type=WizardType.attachments)
        )
        groups = await self.group_service.get_groups_by_ids(
            ids=template_data.get_ids_by_type(wizard_type=WizardType.groups)
        )

        prompt = None
        if template.prompt_text:
            prompt = await self.prompt_service.create_prompt(text=template.prompt_text)

        assistant = self.factory.create_assistant(
            name=name or template.name,
            user=self.user,
            space_id=space.id,
            prompt=prompt,
            completion_model=completion_model,
            attachments=attachments,
            groups=groups,
            template=template,
        )

        return await self.repo.add(assistant)

    def _prepare_public_models(self, space: "Space") -> None:
        pubic_completion_models = self.ai_models_service.db_model_to_public_model(
            models=space.completion_models
        )
        # Only accessible models can be set
        space.completion_models = [m for m in pubic_completion_models if m.can_access]

    async def get_completion_model(self, space: "Space") -> "CompletionModel":
        # FIXME: guarantee all the completion models in space are the `CompletionModelPublic`
        self._prepare_public_models(space=space)
        completion_model = space.get_default_model() or (
            space.get_latest_completion_model()
            if not space.is_personal()
            else await self.ai_models_service.get_latest_available_completion_model()
        )

        if completion_model is None:
            raise BadRequestException(
                "Can not create an assistant in a space without enabled completion models"
            )
        return completion_model

    async def create_default_assistant(self, name: str, space: "Space"):
        completion_model = await self.get_completion_model(space=space)
        assistant = self.factory.create_assistant(
            name=name,
            user=self.user,
            space_id=space.id,
            completion_model=completion_model,
            is_default=True,
        )

        return await self.repo.add(assistant)

    async def update_assistant(
        self,
        id: UUID,
        name: str | None = None,
        prompt: PromptCreate | None = None,
        completion_model_id: UUID | None = None,
        completion_model_kwargs: ModelKwargs | None = None,
        logging_enabled: bool | None = None,
        groups: list[UUID] | None = None,
        websites: list[UUID] | None = None,
        attachment_ids: list[UUID] | None = None,
    ):
        if logging_enabled:
            validate_permission(self.user, Permission.ADMIN)

        assistant = await self.get_assistant(id)
        space = await self._get_space(space_id=assistant.space_id)
        actor = self._get_actor(space=space)

        if not actor.can_edit_assistant(assistant=assistant):
            raise UnauthorizedException()

        if prompt is not None:
            # Create the prompt if the prompt contains text
            # Update the description if the prompt contains description
            if prompt.text is not None:
                prompt = await self.prompt_service.create_prompt(
                    prompt.text, prompt.description
                )

        completion_model = None
        if completion_model_id is not None:
            completion_model = await self.ai_models_service.get_completion_model(
                completion_model_id
            )

        attachments = None
        if attachment_ids is not None:
            attachments = await self.file_service.get_file_infos(attachment_ids)

        if groups is not None:
            groups = await self.group_service.get_groups_by_ids(groups)

        if websites is not None:
            websites = await self.website_service.get_websites_by_ids(websites)

        assistant.update(
            name=name,
            prompt=prompt,
            completion_model=completion_model,
            completion_model_kwargs=completion_model_kwargs,
            attachments=attachments,
            logging_enabled=logging_enabled,
            groups=groups,
            websites=websites,
        )

        self.validate_space_assistant(space, assistant=assistant)

        assistant = await self.repo.update(assistant)

        return assistant

    async def get_assistant(self, id: UUID) -> Assistant:
        assistant = await self.repo.get_by_id(id)

        if assistant is None:
            raise NotFoundException()

        space = await self._get_space(space_id=assistant.space_id)
        actor = self._get_actor(space=space)
        if not actor.can_read_assistants():
            raise UnauthorizedException()

        if assistant.is_default:
            # Add all other assistants in space as
            # tools to the default assistant
            assistant.tool_assistants = space.assistants

        return assistant

    async def get_assistants(
        self, name: str = None, for_tenant: bool = False
    ) -> list[Assistant]:
        if for_tenant:
            return await self.get_tenant_assistants(name)

        return await self.repo.get_for_user(self.user.id, search_query=name)

    @validate_permissions(Permission.ADMIN)
    async def get_tenant_assistants(
        self,
        name: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ):
        assistants = await self.repo.get_for_tenant(
            tenant_id=self.user.tenant_id,
            search_query=name,
            start_date=start_date,
            end_date=end_date,
        )
        return assistants

    async def delete_assistant(self, id: UUID):
        assistant = await self.get_assistant(id)
        space = await self._get_space(space_id=assistant.space_id)
        actor = self._get_actor(space=space)

        if not actor.can_delete_assistant(assistant=assistant):
            raise UnauthorizedException()

        await self.repo.delete(id)

    @validate_permissions(Permission.ADMIN)
    async def generate_api_key(self, assistant_id: UUID):
        assistant = await self.get_assistant(assistant_id)

        return await self.auth_service.create_assistant_api_key(
            "ina", assistant_id=assistant.id
        )

    async def move_assistant_to_space(
        self, assistant_id: UUID, space_id: UUID, move_resources: bool
    ):
        assistant = await self.get_assistant(assistant_id)
        target_space = await self.space_service.get_space(space_id)
        source_space = await self.space_service.get_space(assistant.space_id)
        target_space_actor = self._get_actor(target_space)
        source_space_actor = self._get_actor(source_space)

        if not source_space_actor.can_delete_assistant(assistant=assistant):
            raise UnauthorizedException(
                "User does not have permission to move assistant from space"
            )

        if not target_space_actor.can_create_assistants():
            raise UnauthorizedException(
                "User does not have permission to create assistants in the space"
            )

        if not target_space.is_completion_model_in_space(assistant.completion_model.id):
            raise BadRequestException(
                "Space does not have completion model "
                f"{assistant.completion_model.name} enabled"
            )

        await self.repo.add_assistant_to_space(
            assistant_id=assistant_id, space_id=space_id
        )

        if move_resources:
            for group in assistant.groups:
                await self.group_service.move_group_to_space(
                    group_id=group.id,
                    space_id=space_id,
                    assistant_ids=[assistant_id],
                )

            for website in assistant.websites:
                await self.website_service.move_website_to_space(
                    website_id=website.id,
                    space_id=space_id,
                    assistant_ids=[assistant_id],
                )

    async def get_prompts_by_assistant(self, id: UUID) -> list[Prompt]:
        assistant = await self.get_assistant(id)
        space = await self._get_space(space_id=assistant.space_id)
        actor = self._get_actor(space=space)

        if not actor.can_read_prompts_of_assistant(assistant=assistant):
            raise UnauthorizedException()

        return await self.prompt_service.get_prompts_by_assistant(assistant.id)

    async def _handle_response(
        self,
        response: "CompletionModelResponse",
        datastore_result: "DatastoreResult",
        question: str,
        files: list["File"],
        completion_model: "CompletionModel",
        session: "SessionInDB",
        stream: bool,
        tool_assistant_id: Optional["UUID"] = None,
    ):
        if stream:

            async def response_stream():
                response_string = ""
                async for chunk in response.completion:
                    response_string = f"{response_string}{chunk}"
                    yield response_string, chunk

                total_response_tokens = count_tokens(response_string)
                await self.session_service.add_question_to_session(
                    question=question,
                    answer=response_string,
                    num_tokens_question=response.total_token_count,
                    num_tokens_answer=total_response_tokens,
                    files=files,
                    completion_model=completion_model,
                    info_blob_chunks=datastore_result.no_duplicate_chunks,
                    session=session,
                    logging_details=response.extended_logging,
                    tool_assistant_id=tool_assistant_id,
                )

            return response_stream()
        else:
            answer = response.completion
            total_response_tokens = count_tokens(answer)
            await self.session_service.add_question_to_session(
                question=question,
                answer=answer,
                num_tokens_question=response.total_token_count,
                num_tokens_answer=total_response_tokens,
                files=files,
                completion_model=completion_model,
                info_blob_chunks=datastore_result.no_duplicate_chunks,
                session=session,
                logging_details=response.extended_logging,
                tool_assistant_id=tool_assistant_id,
            )

            return answer

    async def _check_assistant_models(self, assistant: "Assistant"):
        if assistant.completion_model.id is not None:
            completion_model = await self.ai_models_service.get_completion_model(
                assistant.completion_model.id
            )

        if assistant.space_id is not None:
            space = await self.space_service.get_space(assistant.space_id)

            if (
                assistant.completion_model.id
                and not space.is_completion_model_in_space(
                    assistant.completion_model.id
                )
            ):
                raise BadRequestException(
                    f"Completion Model {completion_model.name} is not in space."
                )

            for item in assistant.groups + assistant.websites:
                if not space.is_embedding_model_in_space(item.embedding_model.id):
                    raise BadRequestException(
                        f"Embedding Model {item.embedding_model.name} is not in space."
                    )

    async def ask(
        self,
        question: str,
        assistant_id: "UUID",
        session_id: "UUID" = None,
        file_ids: list["UUID"] = [],
        stream: bool = False,
        tool_assistant_id: Optional["UUID"] = None,
    ):
        active_assistant = await self.get_assistant(id=assistant_id)
        await self._check_assistant_models(assistant=active_assistant)

        if tool_assistant_id is not None:
            tool_assistant = await self.get_assistant(id=tool_assistant_id)
            if tool_assistant_id not in [
                assistant.id for assistant in active_assistant.tool_assistants
            ]:
                raise BadRequestException()

            assistant_to_ask = tool_assistant
        else:
            assistant_to_ask = active_assistant

        cleaned_question = clean_intric_tag(question)
        files = await self.file_service.get_files_by_ids(file_ids=file_ids)

        if session_id is not None:
            session = await self.session_service.get_session_by_uuid(
                id=session_id, assistant_id=assistant_id
            )
        else:
            # Set the name as the question or the filenames
            name = question
            if not name and files:
                name = " ".join(file.name for file in files)

            session = await self.session_service.create_session(
                name=name, assistant=active_assistant
            )

        for _question in session.questions:
            _question.question = clean_intric_tag(_question.question)

        response, datastore_result = await assistant_to_ask.ask(
            question=cleaned_question, session=session, files=files, stream=stream
        )

        answer = await self._handle_response(
            response=response,
            datastore_result=datastore_result,
            question=question,
            files=files,
            completion_model=assistant_to_ask.completion_model,
            session=session,
            stream=stream,
            tool_assistant_id=tool_assistant_id,
        )

        final_response = AssistantResponse(
            question=question,
            files=files,
            session=session,
            answer=answer,
            info_blobs=datastore_result.info_blobs,
            completion_model=assistant_to_ask.completion_model,
            tools=(
                UseTools(assistants=[ModelId(id=tool_assistant_id)])
                if tool_assistant_id is not None
                else UseTools(assistants=[])
            ),
        )

        return final_response

    async def publish_assistant(self, id: UUID, publish: bool):
        assistant = await self.get_assistant(id=id)
        space = await self._get_space(assistant.space_id)
        actor = self._get_actor(space)

        if not actor.can_publish_assistants():
            raise UnauthorizedException()

        assistant.update(published=publish)

        return await self.repo.update(assistant=assistant)
