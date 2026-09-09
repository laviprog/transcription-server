from datetime import UTC, datetime

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}

    def to_dict(self) -> dict:
        return self.model_dump(exclude_unset=True, exclude_none=True)


class HealthCheck(BaseModel):
    status: str = "ok"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
