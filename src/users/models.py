from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base_model import BaseModel

if TYPE_CHECKING:
    from src.api_keys.models import ApiKeyModel


class UserModel(BaseModel):
    """User model."""

    __tablename__ = "users"

    is_active: Mapped[bool] = mapped_column(default=True)
    company_name: Mapped[str | None] = mapped_column(String(255))

    api_keys: Mapped[list[ApiKeyModel]] = relationship(back_populates="user")
