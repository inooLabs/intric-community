from fastapi import Depends

from intric.admin.quota_service import QuotaService
from intric.authentication.auth_dependencies import get_current_active_user
from intric.info_blobs.info_blob_repo import InfoBlobRepository
from intric.server.dependencies.get_repository import get_repository
from intric.users.user import UserInDB


async def get_quota_service(
    user: UserInDB = Depends(get_current_active_user),
    info_blob_repo: InfoBlobRepository = Depends(get_repository(InfoBlobRepository)),
):
    return QuotaService(user, info_blob_repo=info_blob_repo)
