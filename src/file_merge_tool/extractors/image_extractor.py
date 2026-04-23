from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


IMAGE_EXTENSIONS = frozenset(
    {
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    }
)


@dataclass(frozen=True)
class ExtractedImage:
    mime_type: str
    width: int
    height: int
    file_size_bytes: int
    data_uri: str


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def extract_image_file(path: Path) -> ExtractedImage:
    data = path.read_bytes()
    with Image.open(path) as image:
        width, height = image.size

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(data).decode("ascii")
    return ExtractedImage(
        mime_type=mime_type,
        width=width,
        height=height,
        file_size_bytes=len(data),
        data_uri=f"data:{mime_type};base64,{encoded}",
    )
