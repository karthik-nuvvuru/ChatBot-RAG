"""Attachment storage service with local and Azure Blob support."""
import os
import uuid
import logging
from typing import BinaryIO, Optional
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger("conversation_ai.attachments")


class AttachmentService:
    """Service for uploading, downloading, and managing attachments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._blob_client = None
        self._ensure_local_storage()

    def _ensure_local_storage(self):
        """Ensure local storage directory exists."""
        if settings.USE_LOCAL_STORAGE:
            Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    @property
    def blob_client(self):
        """Get Azure Blob client if configured."""
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            return None
        if self._blob_client is None:
            from azure.storage.blob.aio import BlobServiceClient
            self._blob_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
        return self._blob_client

    def _validate_file(self, filename: str, size: int, content_type: str) -> None:
        """Validate file before upload.

        Args:
            filename: Original filename
            size: File size in bytes
            content_type: MIME type

        Raises:
            ValueError: If file is invalid
        """
        max_size = settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
        if size > max_size:
            raise ValueError(
                f"File size {size} exceeds maximum {settings.MAX_ATTACHMENT_SIZE_MB}MB"
            )

        # Log uncommon but allowed types
        allowed_types = [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf", "text/plain", "application/json",
            "application/javascript", "text/html", "text/css",
        ]
        if content_type not in allowed_types:
            logger.warning(f"Uncommon content type uploaded: {content_type}")

    def _generate_storage_path(self, filename: str) -> str:
        """Generate storage path for file.

        Args:
            filename: Original filename

        Returns:
            Storage path string
        """
        date_part = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        unique_id = uuid.uuid4().hex[:12]
        ext = Path(filename).suffix.lower()

        return f"attachments/{date_part}/{unique_id}{ext}"

    async def upload_attachment(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        size: int
    ) -> dict:
        """Upload an attachment.

        Args:
            file: File-like object
            filename: Original filename
            content_type: MIME type
            size: File size in bytes

        Returns:
            Dict with attachment info
        """
        self._validate_file(filename, size, content_type)

        storage_path = self._generate_storage_path(filename)
        attachment_id = uuid.uuid4()

        if settings.USE_LOCAL_STORAGE:
            full_path = Path(settings.LOCAL_STORAGE_PATH) / storage_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Read file content
            content = file.read()

            with open(full_path, "wb") as f:
                f.write(content)

            logger.info(f"Uploaded file to local storage: {full_path}")

        else:
            if not self.blob_client:
                raise RuntimeError("Azure Blob not configured")

            container = self.blob_client.get_container_client(
                settings.AZURE_STORAGE_CONTAINER_NAME
            )

            await container.upload_blob(
                name=storage_path,
                data=file,
                content_type=content_type,
            )

            logger.info(f"Uploaded file to Azure Blob: {storage_path}")

        return {
            "attachment_id": attachment_id,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "storage_path": storage_path,
            "created_at": datetime.now(timezone.utc),
        }

    async def download_attachment(self, storage_path: str) -> Optional[bytes]:
        """Download an attachment.

        Args:
            storage_path: Path to the stored file

        Returns:
            File content as bytes, or None if not found
        """
        if settings.USE_LOCAL_STORAGE:
            full_path = Path(settings.LOCAL_STORAGE_PATH) / storage_path
            if not full_path.exists():
                return None

            with open(full_path, "rb") as f:
                return f.read()

        else:
            if not self.blob_client:
                return None

            try:
                container = self.blob_client.get_container_client(
                    settings.AZURE_STORAGE_CONTAINER_NAME
                )
                blob = container.get_blob_client(storage_path)
                data = await blob.download_blob()
                return await data.readall()
            except Exception as e:
                logger.error(f"Failed to download from Azure: {e}")
                return None

    async def delete_attachment(self, storage_path: str) -> bool:
        """Delete an attachment.

        Args:
            storage_path: Path to the stored file

        Returns:
            True if deleted
        """
        try:
            if settings.USE_LOCAL_STORAGE:
                full_path = Path(settings.LOCAL_STORAGE_PATH) / storage_path
                if full_path.exists():
                    os.remove(full_path)
                    logger.info(f"Deleted local file: {full_path}")
                    return True
                return False

            else:
                if not self.blob_client:
                    return False

                container = self.blob_client.get_container_client(
                    settings.AZURE_STORAGE_CONTAINER_NAME
                )
                await container.delete_blob(storage_path)
                logger.info(f"Deleted Azure blob: {storage_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete attachment: {e}")
            return False

    async def cleanup_orphan_files(self, valid_paths: list) -> int:
        """Clean up files not in valid paths list.

        Args:
            valid_paths: List of valid storage paths

        Returns:
            Number of files deleted
        """
        if settings.USE_LOCAL_STORAGE:
            base_path = Path(settings.LOCAL_STORAGE_PATH) / "attachments"
            if not base_path.exists():
                return 0

            deleted = 0
            for file_path in base_path.rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(base_path))
                    if rel_path not in valid_paths:
                        file_path.unlink()
                        deleted += 1

            return deleted

        return 0

    async def get_storage_stats(self) -> dict:
        """Get storage statistics.

        Returns:
            Dict with storage stats
        """
        if settings.USE_LOCAL_STORAGE:
            base_path = Path(settings.LOCAL_STORAGE_PATH) / "attachments"
            if not base_path.exists():
                return {"total_files": 0, "total_size": 0}

            total_size = 0
            file_count = 0

            for file_path in base_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1

            return {
                "total_files": file_count,
                "total_size": total_size,
                "storage_type": "local"
            }

        return {
            "total_files": 0,
            "total_size": 0,
            "storage_type": "azure"
        }


async def get_attachment_service(db: AsyncSession) -> AttachmentService:
    """Factory to create AttachmentService instance."""
    return AttachmentService(db)