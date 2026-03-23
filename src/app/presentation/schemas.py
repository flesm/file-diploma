from datetime import datetime

from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    file_name: str
    content_type: str
    size: int | None = None
    category: str = "generic"


class MaterialCreateRequest(BaseModel):
    title: str
    description: str = ""
    file_id: str
    audience_scope: str
    target_intern_ids: list[str] = Field(default_factory=list)


class FileAssetResponse(BaseModel):
    id: str
    owner_id: str
    object_key: str
    bucket: str
    file_name: str
    content_type: str
    size: int | None
    category: str
    status: str
    created_at: datetime
    updated_at: datetime


class MaterialResponse(BaseModel):
    id: str
    mentor_id: str
    title: str
    description: str
    file_id: str
    audience_scope: str
    target_intern_ids: list[str]
    created_at: datetime
    updated_at: datetime
