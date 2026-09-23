from pydantic_settings import BaseSettings, SettingsConfigDict

from transcription_server.core.enums import Env, LogLevel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    LOG_LEVEL: LogLevel = LogLevel.INFO
    ENV: Env = Env.PROD

    ROOT_PATH: str | None = None

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0

    TASK_TIME_LIMIT: int = 300
    TASK_RESULT_EXPIRES: int = 3600
    TASK_MAX_RETRIES: int = 3
    TASK_RETRY_BACKOFF: int = 60  # seconds, doubled on every retry
    TASK_RETRY_BACKOFF_MAX: int = 600

    MAX_UPLOAD_SIZE_BYTES: int = 1024 * 1024 * 1024  # 1 GB

    DEVICE: str = "cpu"
    COMPUTE_TYPE: str = "float16"
    DOWNLOAD_ROOT: str = "/data/models"
    BATCH_SIZE: int = 8
    CHUNK_SIZE: int = 30

    TMP_DIR: str = "/data/tmp"

    HF_TOKEN: str | None = None  # Hugging Face token for diarization models

    CORS_ORIGINS: str = ""

    @property
    def IS_DEV(self) -> bool:
        return self.ENV == Env.DEV

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def _DB_URL_BASE(self) -> str:
        return (
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DB_URL_ASYNC(self) -> str:
        return f"postgresql+asyncpg://{self._DB_URL_BASE}"

    @property
    def DB_URL_SYNC(self) -> str:
        return f"postgresql+psycopg2://{self._DB_URL_BASE}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
