from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.app.application.entities import FileAssetEntity, MaterialEntity, ViewerEntity


@pytest.fixture
def mentor_viewer() -> ViewerEntity:
    return ViewerEntity(
        id="mentor-1",
        email="mentor@example.com",
        first_name="Mentor",
        last_name="User",
        role="mentor",
        token="mentor-token",
    )


@pytest.fixture
def intern_viewer() -> ViewerEntity:
    return ViewerEntity(
        id="intern-1",
        email="intern@example.com",
        first_name="Intern",
        last_name="User",
        role="intern",
        token="intern-token",
    )


@pytest.fixture
def file_asset(mentor_viewer: ViewerEntity) -> FileAssetEntity:
    now = datetime.now(timezone.utc)
    return FileAssetEntity(
        id="file-1",
        owner_id=mentor_viewer.id,
        object_key="materials/mentor-1/file-1-spec.pdf",
        bucket="materials",
        file_name="spec.pdf",
        content_type="application/pdf",
        size=128,
        category="materials",
        status="pending_upload",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def material(file_asset: FileAssetEntity) -> MaterialEntity:
    now = datetime.now(timezone.utc)
    return MaterialEntity(
        id="material-1",
        mentor_id="mentor-1",
        title="Architecture",
        description="Read this first",
        file_id=file_asset.id,
        audience_scope="selected_interns",
        target_intern_ids=["intern-1"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def file_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def material_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def storage_gateway() -> AsyncMock:
    gateway = Mock()
    gateway.bucket_name = "materials"
    gateway.presign_upload.return_value = "https://storage/upload"
    gateway.presign_download.return_value = "https://storage/download"
    return gateway


@pytest.fixture
def access_gateway() -> AsyncMock:
    return AsyncMock()
