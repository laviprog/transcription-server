from datetime import UTC, datetime

from advanced_alchemy.extensions.fastapi import service
from fastapi import HTTPException, status

from src.security.hash import hash_key

from .models import ApiKeyModel
from .repositories import ApiKeyRepository


class ApiKeyService(service.SQLAlchemyAsyncRepositoryService[ApiKeyModel, ApiKeyRepository]):
    """API key Service"""

    repository_type = ApiKeyRepository

    def __init__(self, session, **kwargs):
        kwargs.setdefault("auto_commit", True)
        super().__init__(session=session, **kwargs)

    async def validate_api_key(self, api_key_value: str) -> ApiKeyModel:
        api_key_hash = hash_key(api_key_value)

        api_key_model = await self.repository.get_one_or_none(
            *[
                ApiKeyModel.key_hash == api_key_hash,
                ApiKeyModel.deleted_at.is_(None),
                ApiKeyModel.is_active.is_(True),
            ]
        )

        if api_key_model is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        api_key_model.last_used_at = datetime.now(UTC)
        api_key_model = await self.repository.update(api_key_model)
        return api_key_model
