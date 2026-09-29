from transcription_server.core.enums import BaseEnum


class Language(BaseEnum):
    RU = "ru"
    EN = "en"
    DE = "de"
    FR = "fr"
    ES = "es"
    IT = "it"
    PT = "pt"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    UK = "uk"
    AR = "ar"
    HY = "hy"
    KA = "ka"


class Model(BaseEnum):
    SMALL = "small"
    TURBO = "turbo"
    # LARGE_V3_TURBO = "large-v3-turbo"
