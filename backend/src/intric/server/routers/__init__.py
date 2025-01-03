from fastapi import APIRouter

from intric.admin.admin_router import router as admin_router
from intric.ai_models.completion_models.completion_models_router import (
    router as completion_models_router,
)
from intric.ai_models.embedding_models.embedding_models_router import (
    router as embedding_models_router,
)
from intric.allowed_origins.allowed_origin_router import (
    router as allowed_origins_router,
)
from intric.analysis.analysis_router import router as analysis_router
from intric.assistants.api.assistant_router import router as assistants_router
from intric.dashboard.api.dashboard_router import router as dashboard_router
from intric.files.file_router import router as files_router
from intric.groups.group_router import router as groups_router
from intric.info_blobs.info_blobs_router import router as info_blobs_router
from intric.jobs.job_router import router as jobs_router
from intric.limits.limit_router import router as limit_router
from intric.logging.logging_router import router as logging_router
from intric.main.config import get_settings
from intric.prompts.api.prompt_router import router as prompt_router
from intric.server.websockets.websocket_router import router as websocket_router
from intric.services.service_router import router as services_router
from intric.settings.settings_router import router as settings_router
from intric.spaces.api.space_router import router as space_router
from intric.user_groups.user_groups_router import router as user_groups_router
from intric.users.user_router import router as users_router
from intric.websites.website_router import router as website_router
from intric.templates.app_template.api.app_template_router import (
    router as app_template_router,
)
from intric.templates.assistant_template.api.assistant_template_router import (
    router as assistant_template_router,
)
from intric.templates.api.templates_router import router as template_router

router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(info_blobs_router, prefix="/info-blobs", tags=["info-blobs"])
router.include_router(groups_router, prefix="/groups", tags=["groups"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
router.include_router(assistants_router, prefix="/assistants", tags=["assistants"])
router.include_router(services_router, prefix="/services", tags=["services"])
router.include_router(logging_router, prefix="/logging", tags=["logging"])
router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
router.include_router(user_groups_router, prefix="/user-groups", tags=["user-groups"])
router.include_router(
    allowed_origins_router, prefix="/allowed-origins", tags=["allowed-origins"]
)
router.include_router(
    completion_models_router, prefix="/completion-models", tags=["completion-models"]
)
router.include_router(
    embedding_models_router, prefix="/embedding-models", tags=["embedding-models"]
)
router.include_router(files_router, prefix="/files", tags=["files"])
router.include_router(limit_router, prefix="/limits", tags=["limits"])
router.include_router(space_router, prefix="/spaces", tags=["spaces"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
router.include_router(website_router, prefix="/websites", tags=["websites"])
router.include_router(websocket_router, prefix="", tags=["websockets"])
router.include_router(prompt_router, prefix="/prompts", tags=["prompts"])
router.include_router(
    app_template_router,
    prefix="/templates/apps",
    tags=["apps-templates"],
)
router.include_router(
    assistant_template_router,
    prefix="/templates/assistants",
    tags=["assistants-templates"],
)
router.include_router(template_router, prefix="/templates", tags=["templates"])


if get_settings().using_intric_proprietary:
    from intric_prop.prop_routers import include_prop_routers

    include_prop_routers(router)

if get_settings().using_access_management:
    from intric.roles.roles_router import router as roles_router

    router.include_router(roles_router, prefix="/roles", tags=["roles"])
