from enum import StrEnum


class BaseEnum(StrEnum):
    """Base Enum"""

    @classmethod
    def values(cls) -> list[str]:
        """Returns a list of all enum values."""
        return [item.value for item in cls]


class Env(BaseEnum):
    """Environment Enum"""

    DEV = "DEV"
    PROD = "PROD"


class LogLevel(BaseEnum):
    """Log Level Enum"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
