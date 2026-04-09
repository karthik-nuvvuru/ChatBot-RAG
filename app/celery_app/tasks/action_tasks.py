"""Action-related Celery tasks."""
import logging
from datetime import datetime, timezone

from app.celery_app_main import celery_app

logger = logging.getLogger("celery.actions")


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30)
def execute_action(self, action_id: str, action_type: str, params: dict):
    """Execute an action asynchronously.

    Args:
        action_id: UUID of the action
        action_type: Type of action to execute
        params: Action parameters

    Returns:
        Action result dict
    """
    logger.info(f"Executing action {action_id} of type {action_type}")

    try:
        result = {"status": "completed", "action_id": action_id}

        if action_type == "code_execution":
            result["output"] = "Code execution placeholder"
        elif action_type == "web_search":
            result["results"] = []
        elif action_type == "api_call":
            result["response"] = {}

        return result

    except Exception as e:
        logger.error(f"Action {action_id} failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def stream_action_progress(self, action_id: str, progress: float):
    """Stream action progress to WebSocket clients.

    Args:
        action_id: UUID of the action
        progress: Progress percentage (0-100)

    Returns:
        Progress update dict
    """
    logger.debug(f"Action {action_id} progress: {progress}%")

    return {
        "action_id": action_id,
        "progress": progress,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(bind=True)
def notify_action_complete(self, action_id: str, result: dict):
    """Notify clients that an action has completed.

    Args:
        action_id: UUID of the completed action
        result: Action result data

    Returns:
        Completion notification dict
    """
    logger.info(f"Action {action_id} completed")

    return {
        "action_id": action_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "result": result
    }


@celery_app.task(bind=True)
def rollback_action(self, action_id: str, reason: str):
    """Rollback a failed action.

    Args:
        action_id: UUID of the action to rollback
        reason: Reason for rollback

    Returns:
        Rollback confirmation dict
    """
    logger.warning(f"Rolling back action {action_id}: {reason}")

    return {
        "action_id": action_id,
        "rolled_back_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason
    }