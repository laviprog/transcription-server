from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    LOG_LEVEL: str = "INFO"

    ROOT_PATH: str = "/api/v1"

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0

    TASK_TIME_LIMIT: int = 600
    TASK_RESULT_EXPIRES: int = 3600

    DEVICE: str = "cpu"
    COMPUTE_TYPE: str = "float16"
    DOWNLOAD_ROOT: str = "models"
    BATCH_SIZE: int = 8
    CHUNK_SIZE: int = 30

    HF_TOKEN: str | None = None  # Hugging Face token for diarization models

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DB_URL_SYNC(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
