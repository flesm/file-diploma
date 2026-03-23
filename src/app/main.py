from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient

from src.app.application.services import FileApplicationService
from src.app.config import Config
from src.app.infra.access_gateway import AccessGateway
from src.app.infra.minio_gateway import MinioGateway
from src.app.infra.mongo_repositories import MongoFileRepository, MongoMaterialRepository
from src.app.presentation.schemas import (
    FileAssetResponse,
    MaterialCreateRequest,
    MaterialResponse,
    PresignUploadRequest,
)

config = Config()
security = HTTPBearer(auto_error=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo = AsyncIOMotorClient(config.mongo_url)
    db = mongo[config.mongo_db]

    await db.file_assets.create_index("id", unique=True)
    await db.materials.create_index("id", unique=True)
    await db.materials.create_index([("mentor_id", 1), ("created_at", -1)])

    storage = MinioGateway(
        endpoint=config.minio_endpoint,
        public_endpoint=config.minio_public_endpoint,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
        bucket_name=config.minio_bucket,
        secure=config.minio_secure,
    )
    storage.ensure_bucket()

    app.state.mongo = mongo
    app.state.db = db
    app.state.service = FileApplicationService(
        file_repository=MongoFileRepository(db),
        material_repository=MongoMaterialRepository(db),
        storage_gateway=storage,
        access_gateway=AccessGateway(
            auth_api_url=config.auth_api_url,
            core_api_url=config.core_api_url,
        ),
    )

    yield

    mongo.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_viewer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    service: FileApplicationService = app.state.service
    return await service._access_gateway.get_current_user(credentials.credentials)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "File service is running"}


@app.post("/api/v1/files/presign-upload")
async def create_presigned_upload(
    payload: PresignUploadRequest,
    viewer=Depends(get_viewer),
):
    service: FileApplicationService = app.state.service
    return await service.create_upload_link(
        viewer=viewer,
        file_name=payload.file_name,
        content_type=payload.content_type,
        size=payload.size,
        category=payload.category,
    )


@app.post("/api/v1/files/{file_id}/complete", response_model=FileAssetResponse)
async def complete_upload(
    file_id: str,
    viewer=Depends(get_viewer),
):
    service: FileApplicationService = app.state.service
    try:
        asset = await service.complete_upload(viewer, file_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileAssetResponse(**asset.__dict__)


@app.get("/api/v1/files/{file_id}", response_model=FileAssetResponse)
async def get_file_metadata(
    file_id: str,
    _viewer=Depends(get_viewer),
):
    service: FileApplicationService = app.state.service
    try:
        asset = await service.get_file_metadata(file_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return FileAssetResponse(**asset.__dict__)


@app.get("/api/v1/files/{file_id}/download-url")
async def get_download_url(
    file_id: str,
    _viewer=Depends(get_viewer),
):
    service: FileApplicationService = app.state.service
    try:
        return await service.get_download_link(file_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/v1/materials", response_model=MaterialResponse)
async def create_material(
    payload: MaterialCreateRequest,
    viewer=Depends(get_viewer),
):
    service: FileApplicationService = app.state.service
    try:
        material = await service.create_material(
            viewer=viewer,
            title=payload.title,
            description=payload.description,
            file_id=payload.file_id,
            audience_scope=payload.audience_scope,
            target_intern_ids=payload.target_intern_ids,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return MaterialResponse(**material.__dict__)


@app.get("/api/v1/materials", response_model=list[MaterialResponse])
async def list_materials(viewer=Depends(get_viewer)):
    service: FileApplicationService = app.state.service
    materials = await service.list_materials_for_viewer(viewer)
    return [MaterialResponse(**item.__dict__) for item in materials]
