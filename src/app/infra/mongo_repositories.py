from datetime import datetime
from typing import Any

from src.app.application.entities import FileAssetEntity, MaterialEntity


def serialize_datetime(value: datetime) -> str:
    return value.isoformat()


class MongoFileRepository:
    def __init__(self, db):
        self._collection = db.file_assets

    async def create(self, asset: FileAssetEntity) -> None:
        await self._collection.insert_one(asset.__dict__)

    async def get_by_id(self, file_id: str) -> FileAssetEntity | None:
        document = await self._collection.find_one({"id": file_id})
        return FileAssetEntity(**self._strip_mongo_id(document)) if document else None

    async def update(self, asset: FileAssetEntity) -> None:
        await self._collection.replace_one({"id": asset.id}, asset.__dict__, upsert=False)

    @staticmethod
    def _strip_mongo_id(document):
        if not document:
            return document
        next_document = dict(document)
        next_document.pop("_id", None)
        return next_document


class MongoMaterialRepository:
    def __init__(self, db):
        self._collection = db.materials

    async def create(self, material: MaterialEntity) -> None:
        await self._collection.insert_one(material.__dict__)

    async def list_all(self) -> list[MaterialEntity]:
        documents = await self._collection.find({}).sort("created_at", -1).to_list(length=500)
        return [MaterialEntity(**self._strip_mongo_id(item)) for item in documents]

    @staticmethod
    def _strip_mongo_id(document):
        if not document:
            return document
        next_document = dict(document)
        next_document.pop("_id", None)
        return next_document
