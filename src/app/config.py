from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.example", extra="ignore")

    mongo_url: str = Field(alias="MONGO_URL")
    mongo_db: str = Field(alias="MONGO_DB")
    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_public_endpoint: str = Field(alias="MINIO_PUBLIC_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(alias="MINIO_BUCKET")
    minio_secure: bool = Field(alias="MINIO_SECURE")
    auth_api_url: str = Field(alias="AUTH_API_URL")
    core_api_url: str = Field(alias="CORE_API_URL")
