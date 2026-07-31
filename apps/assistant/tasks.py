from celery import shared_task


@shared_task
def task_reindex_all() -> dict:
    from apps.assistant.services.indexing import reindex_all

    return reindex_all()


@shared_task
def ping() -> str:
    return "pong"
