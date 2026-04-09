"""Session-related Celery tasks."""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_

from app.core.config import settings
from app.celery_app_instance import celery_app

logger = logging.getLogger("celery.session")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def archive_inactive_sessions(self):
    """Archive sessions inactive for more than threshold days.

    Runs daily at 2 AM UTC.
    """
    logger.info("Starting archive inactive sessions task")

    try:
        from app.db.session import get_db_session
        from app.models import ConversationSession, SessionStatus

        threshold = datetime.now(timezone.utc) - timedelta(
            days=settings.SESSION_INACTIVITY_THRESHOLD_DAYS
        )
        archived_count = 0
        batch_size = settings.SESSION_ARCHIVE_BATCH_SIZE

        async def run_archive():
            nonlocal archived_count
            db = await get_db_session()
            try:
                while True:
                    result = await db.execute(
                        select(ConversationSession).where(
                            and_(
                                ConversationSession.status == SessionStatus.ACTIVE,
                                ConversationSession.last_active_at < threshold
                            )
                        ).limit(batch_size)
                    )
                    sessions = result.scalars().all()

                    if not sessions:
                        break

                    for session in sessions:
                        session.status = SessionStatus.ARCHIVED
                        session.updated_at = datetime.now(timezone.utc)
                        archived_count += 1

                    await db.commit()
                    logger.info(f"Archived batch of {len(sessions)} sessions")

            finally:
                await db.close()

        import asyncio
        asyncio.run(run_archive())

        logger.info(f"Archive task completed. Total archived: {archived_count}")
        return {"archived_count": archived_count}

    except Exception as e:
        logger.error(f"Archive task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def update_session_metrics(self, session_id: str):
    """Update metrics for a session.

    Args:
        session_id: UUID of the session
    """
    logger.info(f"Updating metrics for session {session_id}")

    try:
        from app.db.session import get_db_session
        from app.models import ConversationSession

        async def run_update():
            db = await get_db_session()
            try:
                result = await db.execute(
                    select(ConversationSession).where(
                        ConversationSession.session_id == session_id
                    )
                )
                session = result.scalar_one_or_none()
                if session:
                    # Could update additional metrics here
                    pass
            finally:
                await db.close()

        import asyncio
        asyncio.run(run_update())

        return {"session_id": session_id, "status": "updated"}

    except Exception as e:
        logger.error(f"Update metrics task failed: {e}")
        return {"session_id": session_id, "status": "failed", "error": str(e)}


@celery_app.task(bind=True)
def cleanup_abandoned_sessions(self):
    """Clean up sessions that were never activated.

    Removes sessions in 'paused' status for >30 days.
    """
    logger.info("Starting cleanup abandoned sessions task")

    try:
        from app.db.session import get_db_session
        from app.models import ConversationSession, SessionStatus

        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        deleted_count = 0

        async def run_cleanup():
            nonlocal deleted_count
            db = await get_db_session()
            try:
                result = await db.execute(
                    select(ConversationSession).where(
                        and_(
                            ConversationSession.status == SessionStatus.PAUSED,
                            ConversationSession.last_active_at < threshold
                        )
                    )
                )
                sessions = result.scalars().all()

                for session in sessions:
                    await db.delete(session)
                    deleted_count += 1

                await db.commit()

            finally:
                await db.close()

        import asyncio
        asyncio.run(run_cleanup())

        logger.info(f"Cleanup task completed. Deleted: {deleted_count}")
        return {"deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"deleted_count": 0, "error": str(e)}