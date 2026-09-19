import asyncio
import contextlib
import re
import tempfile
from pathlib import Path

from fastapi import UploadFile

from transcription_server.core.config import settings
from transcription_server.core.utils import remove_file

ALLOWED_EXT = {".wav", ".mp3"}

BASE_TMP_DIR = Path(settings.TMP_DIR)
BASE_TMP_DIR.mkdir(parents=True, exist_ok=True)

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
CHUNK = 1024 * 1024  # 1 MB


class UploadError(Exception):
    """Base class for upload failures."""


class UnsupportedFileTypeError(UploadError):
    """Raised when the uploaded file has an extension we do not accept."""


class EmptyFileError(UploadError):
    """Raised when the uploaded file contains no data."""


class FileTooLargeError(UploadError):
    """Raised when the uploaded file exceeds MAX_UPLOAD_SIZE_BYTES."""


def _sanitize(name: str) -> str:
    name = name or "audio"
    name = _SAFE.sub("_", name)
    return name[:128]


def _write_upload_sync(file: UploadFile, ext: str) -> str:
    max_size = settings.MAX_UPLOAD_SIZE_BYTES
    written = 0

    with tempfile.NamedTemporaryFile(
        mode="wb", prefix="stt_", suffix=ext, dir=BASE_TMP_DIR, delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)
        try:
            file.file.seek(0)
            while True:
                chunk = file.file.read(CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_size:
                    raise FileTooLargeError(
                        f"File exceeds the maximum allowed size of {max_size} bytes"
                    )
                tmp.write(chunk)
            if written == 0:
                raise EmptyFileError("Uploaded file is empty")
        except BaseException:
            # Never leave a partial upload behind on the shared volume.
            with contextlib.suppress(OSError):
                tmp.close()
            remove_file(tmp_path)
            raise

    return str(tmp_path.resolve())


async def save_upload_to_temp(file: UploadFile) -> str:
    orig = _sanitize(file.filename or "audio")
    ext = Path(orig).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {ext or 'no extension'} (allowed: {', '.join(ALLOWED_EXT)})"
        )

    return await asyncio.to_thread(_write_upload_sync, file, ext)
