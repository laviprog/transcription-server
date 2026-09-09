from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base_model import BaseModel


class AdminModel(BaseModel):
    """Admin model."""

    __tablename__ = "admins"

    email: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
