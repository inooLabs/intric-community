from intric.main.config import get_settings
from intric.worker.routes import worker as sub_worker
from intric.worker.worker import Worker

worker = Worker()
worker.include_subworker(sub_worker)


if get_settings().using_intric_proprietary:
    from intric_prop.apps.app_runs.api.app_run_worker import worker as app_worker
    from intric_prop.worker.prop_routes import worker as prop_worker

    worker.include_subworker(prop_worker)
    worker.include_subworker(app_worker)


class WorkerSettings:
    functions = worker.functions
    cron_jobs = worker.cron_jobs
    redis_settings = worker.redis_settings
    on_startup = worker.on_startup
    on_shutdown = worker.on_shutdown
    retry_jobs = worker.retry_jobs
    job_timeout = worker.job_timeout
    max_jobs = worker.max_jobs
    expires_extra_ms = worker.expires_extra_ms
