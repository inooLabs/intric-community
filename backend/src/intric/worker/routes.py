from intric.jobs.task_models import Transcription, UploadInfoBlob
from intric.main.container.container import Container
from intric.main.logging import get_logger
from intric.worker.tasks import transcription_task, upload_info_blob_task
from intric.worker.worker import Worker

logger = get_logger(__name__)

worker = Worker()


@worker.function()
async def upload_info_blob(job_id: str, params: UploadInfoBlob, container: Container):
    return await upload_info_blob_task(
        job_id=job_id, params=params, container=container
    )


@worker.function()
async def transcription(job_id: str, params: Transcription, container: Container):
    return await transcription_task(job_id=job_id, params=params, container=container)
