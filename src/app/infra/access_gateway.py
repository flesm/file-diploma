from typing import Any

import httpx
from fastapi import HTTPException, status

from src.app.application.entities import ViewerEntity


class AccessGateway:
    def __init__(self, auth_api_url: str, core_api_url: str):
        self._auth_api_url = auth_api_url
        self._core_api_url = core_api_url

    async def get_current_user(self, token: str) -> ViewerEntity:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self._auth_api_url}/auth/me",
                params={"token": token},
            )

        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        payload = response.json()
        return ViewerEntity(
            id=str(payload["id"]),
            email=payload["email"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            role=payload.get("role"),
            token=token,
        )

    async def get_mentor_intern_ids(self, token: str) -> list[str]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self._core_api_url}/mentor-intern-links",
                headers={"Authorization": f"Bearer {token}"},
            )

        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot load mentor interns")

        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [str(item["intern_id"]) for item in payload]

    async def get_my_mentor_id(self, token: str) -> str | None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self._core_api_url}/mentor-intern-links/my-mentor",
                headers={"Authorization": f"Bearer {token}"},
            )

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot load mentor")

        payload = response.json()
        return str(payload["mentor_id"]) if isinstance(payload, dict) else None
