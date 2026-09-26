from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class ReceiptData:
    original_name: str
    content_type: str
    size: int


def _read_header(upload, length: int = 16) -> bytes:
    position = upload.tell()
    upload.seek(0)
    header = upload.read(length)
    upload.seek(position)
    return header


def validate_receipt(upload) -> ReceiptData:
    max_bytes = int(settings.PIXU_RECEIPT_MAX_BYTES)
    allowed_types = set(settings.PIXU_RECEIPT_ALLOWED_TYPES)
    content_type = (getattr(upload, "content_type", "") or "").lower()
    original_name = Path(getattr(upload, "name", "comprovante")).name
    size = int(getattr(upload, "size", 0) or 0)
    if size <= 0 or size > max_bytes:
        raise ValidationError(
            _("O comprovante deve ter entre 1 byte e %(limit)s MB.")
            % {"limit": max_bytes // (1024 * 1024)},
        )
    if content_type not in allowed_types:
        raise ValidationError(_("Envie um comprovante em PDF, JPEG ou PNG."))
    header = _read_header(upload)
    valid_signature = {
        "application/pdf": header.startswith(b"%PDF"),
        "image/jpeg": header.startswith(b"\xff\xd8\xff"),
        "image/png": header.startswith(b"\x89PNG\r\n\x1a\n"),
    }.get(content_type, False)
    if not valid_signature:
        raise ValidationError(
            _("O conteúdo do comprovante não corresponde ao tipo informado."),
        )
    return ReceiptData(
        original_name=original_name[:255],
        content_type=content_type,
        size=size,
    )
