"""Attachment-related Celery tasks."""
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.core.config import settings
from app.celery_app_instance import celery_app

logger = logging.getLogger("celery.attachments")


@celery_app.task(bind=True, max_retries=3)
def cleanup_old_attachments(self):
    """Delete attachments older than retention period.

    Runs weekly on Sunday at 3 AM.
    """
    logger.info("Starting attachment cleanup task")

    try:
        retention_days = settings.ATTACHMENT_CLEANUP_DAYS
        threshold = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted_count = 0
        freed_bytes = 0

        if settings.USE_LOCAL_STORAGE:
            base_path = Path(settings.LOCAL_STORAGE_PATH) / "attachments"

            if base_path.exists():
                for file_path in base_path.rglob("*"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

                        if mtime < threshold:
                            file_size = stat.st_size
                            file_path.unlink()
                            deleted_count += 1
                            freed_bytes += file_size

        logger.info(
            f"Attachment cleanup completed. "
            f"Deleted: {deleted_count}, Freed: {freed_bytes} bytes"
        )

        return {
            "deleted_count": deleted_count,
            "freed_bytes": freed_bytes
        }

    except Exception as e:
        logger.error(f"Attachment cleanup task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def scan_attachments_for_viruses(self, attachment_path: str):
    """Placeholder for virus scanning.

    In production, integrate with ClamAV or similar.

    Args:
        attachment_path: Path to the attachment to scan

    Returns:
        Scan result dict
    """
    logger.info(f"Scanning attachment: {attachment_path}")

    # Placeholder implementation
    # In production: call ClamAV API or similar
    return {
        "path": attachment_path,
        "status": "clean",
        "scanned_at": datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(bind=True)
def verify_attachment_integrity(self, attachment_path: str):
    """Verify attachment integrity after upload.

    Args:
        attachment_path: Path to verify

    Returns:
        Verification result dict
    """
    logger.info(f"Verifying attachment: {attachment_path}")

    if settings.USE_LOCAL_STORAGE:
        full_path = Path(settings.LOCAL_STORAGE_PATH) / attachment_path
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0

        return {
            "path": attachment_path,
            "exists": exists,
            "size": size,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

    return {
        "path": attachment_path,
        "exists": False,
        "size": 0,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(bind=True)
def generate_thumbnail(self, attachment_path: str):
    """Generate thumbnail for image attachments.

    Args:
        attachment_path: Path to the image

    Returns:
        Thumbnail result dict
    """
    logger.info(f"Generating thumbnail for: {attachment_path}")

    # Placeholder - implement with Pillow in production
    return {
        "path": attachment_path,
        "thumbnail_path": f"{attachment_path}.thumb",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }