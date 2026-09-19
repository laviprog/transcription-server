from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from transcription_server.core.database.config import sqlalchemy_config
from transcription_server.domain.api_keys.services import ApiKeyService


async def provide_api_key_service() -> AsyncGenerator[ApiKeyService, None]:
    async with ApiKeyService.new(config=sqlalchemy_config) as service:
        yield service


type ApiKeyServiceDep = Annotated[ApiKeyService, Depends(provide_api_key_service)]
