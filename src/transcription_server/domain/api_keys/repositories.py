from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from transcription_server.domain.api_keys.models import ApiKeyModel


class ApiKeyRepository(SQLAlchemyAsyncRepository[ApiKeyModel]):
    """Api key repository"""

    model_type = ApiKeyModel
