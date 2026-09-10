import wave
from pathlib import Path


def get_filesize_bytes(path: str) -> int:
    return Path(path).stat().st_size


def wav_duration_seconds(path: str) -> float:
    with wave.open(path, "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate()
        return frames / float(rate)


def mp3_duration_seconds(path: str) -> float | None:
    from mutagen.mp3 import MP3

    # A missing or corrupt file raises MutagenError, which the caller already handles.
    info = MP3(path).info
    return float(info.length) if info is not None else None


def get_duration_seconds(path: str) -> float | None:
    suffix = Path(path).suffix.lower()
    if suffix == ".wav":
        return wav_duration_seconds(path)
    if suffix == ".mp3":
        return mp3_duration_seconds(path)
    return None
