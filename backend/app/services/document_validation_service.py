from io import BytesIO

import fitz
from PIL import Image


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


class FileValidationResult:
    def __init__(
        self,
        is_valid: bool,
        file_type: str | None = None,
        file_size_bytes: int | None = None,
        page_count: int | None = None,
        errors: list[str] | None = None,
    ):
        self.is_valid = is_valid
        self.file_type = file_type
        self.file_size_bytes = file_size_bytes
        self.page_count = page_count
        self.errors = errors or []

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "errors": self.errors,
        }


def validate_document(
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
    max_file_size_mb: int = 10,
    max_pages: int = 3,
) -> FileValidationResult:

    errors: list[str] = []

    # ---------------------------------------------------------
    # 1. Check filename
    # ---------------------------------------------------------
    if not filename:
        errors.append("Filename is required.")

    extension = ""

    if filename:
        extension = "." + filename.rsplit(".", 1)[-1].lower()

    # ---------------------------------------------------------
    # 2. Check file extension
    # ---------------------------------------------------------
    if extension not in ALLOWED_EXTENSIONS:
        errors.append(
            "Unsupported file type. Only PDF, JPG and PNG are supported."
        )

    # ---------------------------------------------------------
    # 3. Check MIME/content type
    # ---------------------------------------------------------
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        errors.append(
            "Unsupported content type. Only PDF, JPG and PNG are supported."
        )

    # ---------------------------------------------------------
    # 4. Check empty file
    # ---------------------------------------------------------
    file_size = len(file_bytes)

    if file_size == 0:
        errors.append("The uploaded file is empty.")

    # ---------------------------------------------------------
    # 5. Check maximum file size
    # ---------------------------------------------------------
    max_file_size_bytes = max_file_size_mb * 1024 * 1024

    if file_size > max_file_size_bytes:
        errors.append(
            f"File size exceeds the maximum allowed size of "
            f"{max_file_size_mb} MB."
        )

    # ---------------------------------------------------------
    # If basic checks already failed, stop before opening file
    # ---------------------------------------------------------
    if errors:
        return FileValidationResult(
            is_valid=False,
            file_type=content_type,
            file_size_bytes=file_size,
            page_count=None,
            errors=errors,
        )

    # ---------------------------------------------------------
    # 6. Validate PDF
    # ---------------------------------------------------------
    if extension == ".pdf":

        try:
            pdf_document = fitz.open(
                stream=file_bytes,
                filetype="pdf",
            )

            page_count = len(pdf_document)

            if page_count == 0:
                errors.append("The PDF contains no pages.")

            elif page_count > max_pages:
                errors.append(
                    f"PDF contains {page_count} pages. "
                    f"The maximum allowed is {max_pages} pages."
                )

            pdf_document.close()

            return FileValidationResult(
                is_valid=len(errors) == 0,
                file_type=content_type,
                file_size_bytes=file_size,
                page_count=page_count,
                errors=errors,
            )

        except Exception:
            return FileValidationResult(
                is_valid=False,
                file_type=content_type,
                file_size_bytes=file_size,
                page_count=None,
                errors=[
                    "The uploaded PDF is corrupted or cannot be read."
                ],
            )

    # ---------------------------------------------------------
    # 7. Validate JPG / PNG
    # ---------------------------------------------------------
    if extension in {".jpg", ".jpeg", ".png"}:

        try:
            image = Image.open(BytesIO(file_bytes))

            # Verify checks the image data without loading it fully.
            image.verify()

            return FileValidationResult(
                is_valid=True,
                file_type=content_type,
                file_size_bytes=file_size,
                page_count=1,
                errors=[],
            )

        except Exception:
            return FileValidationResult(
                is_valid=False,
                file_type=content_type,
                file_size_bytes=file_size,
                page_count=None,
                errors=[
                    "The uploaded image is corrupted or cannot be read."
                ],
            )

    # ---------------------------------------------------------
    # 8. Safety fallback
    # ---------------------------------------------------------
    return FileValidationResult(
        is_valid=False,
        file_type=content_type,
        file_size_bytes=file_size,
        page_count=None,
        errors=["The uploaded file could not be validated."],
    )