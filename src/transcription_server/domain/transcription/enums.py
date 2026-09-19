from transcription_server.core.enums import BaseEnum


class Language(BaseEnum):
    RU = "ru"
    EN = "en"


class Model(BaseEnum):
    SMALL = "small"
    TURBO = "turbo"
    # LARGE_V3_TURBO = "large-v3-turbo"
