from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.app.application.entities import FileAssetEntity, MaterialEntity, ViewerEntity


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FileApplicationService:
    def __init__(self, file_repository, material_repository, storage_gateway, access_gateway):
        self._file_repository = file_repository
        self._material_repository = material_repository
        self._storage_gateway = storage_gateway
        self._access_gateway = access_gateway

    async def create_upload_link(
        self,
        viewer: ViewerEntity,
        file_name: str,
        content_type: str,
        size: int | None,
        category: str,
    ) -> dict[str, Any]:
        now = utc_now()
        object_key = f"{category}/{viewer.id}/{uuid4()}-{file_name}"
        file_id = str(uuid4())
        asset = FileAssetEntity(
            id=file_id,
            owner_id=viewer.id,
            object_key=object_key,
            bucket=self._storage_gateway.bucket_name,
            file_name=file_name,
            content_type=content_type,
            size=size,
            category=category,
            status="pending_upload",
            created_at=now,
            updated_at=now,
        )
        await self._file_repository.create(asset)
        upload_url = self._storage_gateway.presign_upload(object_key, content_type)
        return {
            "file_id": file_id,
            "upload_url": upload_url,
            "object_key": object_key,
            "bucket": self._storage_gateway.bucket_name,
        }

    async def complete_upload(self, viewer: ViewerEntity, file_id: str) -> FileAssetEntity:
        asset = await self._file_repository.get_by_id(file_id)
        if not asset or asset.owner_id != viewer.id:
            raise ValueError("File not found")

        self._storage_gateway.ensure_object_exists(asset.object_key)
        asset.status = "uploaded"
        asset.updated_at = utc_now()
        await self._file_repository.update(asset)
        return asset

    async def get_download_link(self, file_id: str) -> dict[str, str]:
        asset = await self._file_repository.get_by_id(file_id)
        if not asset:
            raise ValueError("File not found")
        return {
            "file_id": file_id,
            "download_url": self._storage_gateway.presign_download(asset.object_key),
            "file_name": asset.file_name,
        }

    async def get_file_metadata(self, file_id: str) -> FileAssetEntity:
        asset = await self._file_repository.get_by_id(file_id)
        if not asset:
            raise ValueError("File not found")
        return asset

    async def create_material(
        self,
        viewer: ViewerEntity,
        title: str,
        description: str,
        file_id: str,
        audience_scope: str,
        target_intern_ids: list[str],
    ) -> MaterialEntity:
        if viewer.role != "mentor":
            raise ValueError("Only mentor can create materials")

        asset = await self._file_repository.get_by_id(file_id)
        if not asset:
            raise ValueError("File not found")

        linked_intern_ids = await self._access_gateway.get_mentor_intern_ids(viewer.token)
        if audience_scope == "selected_interns":
            if not target_intern_ids:
                raise ValueError("Select at least one intern")
            if not set(target_intern_ids).issubset(set(linked_intern_ids)):
                raise ValueError("Some interns are not assigned to mentor")
        elif audience_scope == "own_interns":
            target_intern_ids = linked_intern_ids
        else:
            target_intern_ids = []

        now = utc_now()
        material = MaterialEntity(
            id=str(uuid4()),
            mentor_id=viewer.id,
            title=title,
            description=description,
            file_id=file_id,
            audience_scope=audience_scope,
            target_intern_ids=target_intern_ids,
            created_at=now,
            updated_at=now,
        )
        await self._material_repository.create(material)
        return material

    async def list_materials_for_viewer(self, viewer: ViewerEntity) -> list[MaterialEntity]:
        materials = await self._material_repository.list_all()
        if viewer.role == "mentor":
            return [item for item in materials if item.mentor_id == viewer.id]

        mentor_id = await self._access_gateway.get_my_mentor_id(viewer.token)
        visible_materials = []
        for item in materials:
            if item.audience_scope == "all_interns":
                visible_materials.append(item)
                continue
            if item.mentor_id != mentor_id:
                continue
            if item.audience_scope == "own_interns":
                visible_materials.append(item)
                continue
            if viewer.id in item.target_intern_ids:
                visible_materials.append(item)

        return visible_materials
