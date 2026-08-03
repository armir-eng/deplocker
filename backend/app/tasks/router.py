from celery.result import AsyncResult
from fastapi import APIRouter

from .celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}", summary="Task information tracking endpoint")
async def get_task_status(task_id: str) -> dict[str, str | None]:
    task_result: AsyncResult = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": str(task_result.result) if task_result.ready() else None,
    }
