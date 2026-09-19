from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from transcription_server.api.api_keys.dependencies import ApiKeyServiceDep


async def verify_api_key(
    api_key_service: ApiKeyServiceDep, authorization: str = Header(...)
) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    api_key_value = authorization.removeprefix("Bearer ").strip()

    api_key = await api_key_service.validate_api_key(api_key_value)

    return api_key.id


type ApiKeyIdDep = Annotated[UUID, Depends(verify_api_key)]
