from io import BytesIO

from PIL import Image

from app.services.document_validation_service import validate_document


def create_test_png():
    image = Image.new("RGB", (100, 100), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_valid_png_document():
    png_bytes = create_test_png()

    result = validate_document(
        filename="test.png",
        content_type="image/png",
        file_bytes=png_bytes,
        max_file_size_mb=10,
        max_pages=3,
    )

    assert result.is_valid is True
    assert result.file_type == "image/png"
    assert result.file_size_bytes > 0


def test_unsupported_file_type():
    result = validate_document(
        filename="test.exe",
        content_type="application/octet-stream",
        file_bytes=b"test",
        max_file_size_mb=10,
        max_pages=3,
    )

    assert result.is_valid is False
    assert len(result.errors) > 0


def test_empty_file():
    result = validate_document(
        filename="empty.pdf",
        content_type="application/pdf",
        file_bytes=b"",
        max_file_size_mb=10,
        max_pages=3,
    )

    assert result.is_valid is False
    assert len(result.errors) > 0
