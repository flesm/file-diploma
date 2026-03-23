from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ViewerEntity:
    id: str
    email: str
    first_name: str
    last_name: str
    role: str | None
    token: str


@dataclass
class FileAssetEntity:
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


@dataclass
class MaterialEntity:
    id: str
    mentor_id: str
    title: str
    description: str
    file_id: str
    audience_scope: str
    target_intern_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
