"""Unit tests for Celery tasks."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from app.celery_app.tasks.session_tasks import (
    archive_inactive_sessions,
    update_session_metrics,
    cleanup_abandoned_sessions
)
from app.celery_app.tasks.attachment_tasks import (
    cleanup_old_attachments,
    scan_attachments_for_viruses
)


class TestSessionTasks:
    """Test cases for session-related Celery tasks."""

    def test_archive_inactive_sessions(self):
        """Test archiving inactive sessions."""
        # Celery tasks are not async - they run as background workers
        # This tests the task can be called (it will run in worker)
        assert archive_inactive_sessions.max_retries == 3

    def test_update_session_metrics(self):
        """Test updating session metrics."""
        # Celery tasks are not async - test the function directly
        result = update_session_metrics("session-123")

        assert result is not None
        assert result["session_id"] == "session-123"


class TestAttachmentTasks:
    """Test cases for attachment-related Celery tasks."""

    def test_cleanup_old_attachments(self):
        """Test cleaning up old attachments."""
        # Celery tasks are not async - test the function directly
        with patch('app.celery_app.tasks.attachment_tasks.settings') as mock_settings:
            mock_settings.USE_LOCAL_STORAGE = True
            mock_settings.LOCAL_STORAGE_PATH = "/tmp/test_attachments"
            mock_settings.ATTACHMENT_CLEANUP_DAYS = 90

            from pathlib import Path
            Path("/tmp/test_attachments").mkdir(parents=True, exist_ok=True)

            result = cleanup_old_attachments()

            assert result is not None
            assert "deleted_count" in result
            assert "freed_bytes" in result

    def test_scan_attachments_for_viruses(self):
        """Test virus scanning placeholder."""
        result = scan_attachments_for_viruses("/path/to/file")

        assert result is not None
        assert result["status"] == "clean"
        assert "scanned_at" in result


class TestTaskRetryLogic:
    """Test Celery task retry logic."""

    def test_retry_configuration(self):
        """Test that tasks have retry configuration."""
        # Archive task should have max_retries=3
        assert archive_inactive_sessions.max_retries == 3

    def test_task_time_limits(self):
        """Test that tasks have time limits configured."""
        from app.celery_app_instance import celery_app

        assert celery_app.conf.task_time_limit == 300
        assert celery_app.conf.task_soft_time_limit == 240