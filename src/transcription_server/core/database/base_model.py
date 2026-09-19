from advanced_alchemy.base import UUIDAuditBase

from transcription_server.core.database.mixins.soft_delete_mixin import SoftDeleteMixin


class BaseModel(SoftDeleteMixin, UUIDAuditBase):
    """Base model with UUID primary key, audit fields, and soft delete functionality."""

    __abstract__ = True

    pass
