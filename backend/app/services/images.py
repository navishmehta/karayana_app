"""Safe image uploads.

The upload is opened with Pillow, checked (type, size, pixel count) and re-encoded to WebP in two sizes.
The original bytes are never stored, so EXIF/GPS data or anything hidden in the file is dropped.
"""

import uuid
from dataclasses import dataclass
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.constants import (
    IMAGE_ALLOWED_FORMATS,
    IMAGE_FULL_WIDTH,
    IMAGE_MAX_PIXELS,
    IMAGE_MAX_UPLOAD_BYTES,
    IMAGE_THUMB_WIDTH,
    IMAGE_WEBP_QUALITY,
)
from app.core.errors import AppError
from app.enums.catalogue import MediaFolder
from app.enums.error_code import ErrorCode
from app.services.storage import get_storage

Image.MAX_IMAGE_PIXELS = IMAGE_MAX_PIXELS


@dataclass(frozen=True)
class StoredImage:
    path: str
    thumb_path: str


def _read_limited(upload: UploadFile) -> bytes:
    data = upload.file.read(IMAGE_MAX_UPLOAD_BYTES + 1)
    if len(data) > IMAGE_MAX_UPLOAD_BYTES:
        raise AppError(ErrorCode.IMAGE_TOO_LARGE)
    return data


def _open(data: bytes) -> Image.Image:
    try:
        with Image.open(BytesIO(data)) as probe:
            if probe.format not in IMAGE_ALLOWED_FORMATS:
                raise AppError(ErrorCode.INVALID_IMAGE)
            probe.verify()
        image = Image.open(BytesIO(data))
        image.load()
    except AppError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise AppError(ErrorCode.INVALID_IMAGE) from exc
    image = ImageOps.exif_transpose(image)  # respect phone camera rotation before EXIF is dropped
    return image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")


def _webp(image: Image.Image, width: int) -> bytes:
    resized = image.copy()
    if resized.width > width:
        resized.thumbnail((width, width * 10), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    resized.save(buffer, format="WEBP", quality=IMAGE_WEBP_QUALITY, method=4)
    return buffer.getvalue()


def store_image(upload: UploadFile, folder: MediaFolder) -> StoredImage:
    image = _open(_read_limited(upload))
    name = f"{folder.value}/{uuid.uuid4().hex}"
    stored = StoredImage(path=f"{name}.webp", thumb_path=f"{name}_thumb.webp")
    storage = get_storage()
    storage.save(stored.path, _webp(image, IMAGE_FULL_WIDTH))
    storage.save(stored.thumb_path, _webp(image, IMAGE_THUMB_WIDTH))
    return stored
