from io import BytesIO

import fitz
from PIL import Image


class OCRResult:
    def __init__(
        self,
        text: str,
        ocr_used: bool,
        page_count: int,
        pages: list[dict],
    ):
        self.text = text
        self.ocr_used = ocr_used
        self.page_count = page_count
        self.pages = pages

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "ocr_used": self.ocr_used,
            "page_count": self.page_count,
            "pages": self.pages,
        }


def extract_text_from_pdf(file_bytes: bytes) -> OCRResult:
    """
    Extract text from a native PDF.

    If a PDF contains little or no embedded text, it is marked
    as requiring OCR. Actual OCR will be connected later.
    """

    pdf = fitz.open(
        stream=file_bytes,
        filetype="pdf",
    )

    pages = []
    all_text = []
    total_text_length = 0

    for page_number, page in enumerate(pdf, start=1):
        text = page.get_text("text").strip()

        pages.append(
            {
                "page_number": page_number,
                "text": text,
            }
        )

        if text:
            all_text.append(text)
            total_text_length += len(text)

    page_count = len(pdf)

    pdf.close()

    # A scanned/image-only PDF usually has no useful embedded text.
    # We mark it for OCR rather than pretending that extraction succeeded.
    ocr_needed = total_text_length < 20

    return OCRResult(
        text="\n\n".join(all_text),
        ocr_used=ocr_needed,
        page_count=page_count,
        pages=pages,
    )


def extract_text_from_image(file_bytes: bytes) -> OCRResult:
    """
    Validate/read a JPG or PNG image.

    Actual OCR will be connected in the next extraction stage.
    """

    image = Image.open(BytesIO(file_bytes))

    # Load the image to make sure its pixel data can actually be read.
    image.load()

    return OCRResult(
        text="",
        ocr_used=True,
        page_count=1,
        pages=[
            {
                "page_number": 1,
                "text": "",
            }
        ],
    )


def extract_document_text(
    file_bytes: bytes,
    file_type: str,
) -> OCRResult:

    if file_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)

    if file_type in {"image/jpeg", "image/png"}:
        return extract_text_from_image(file_bytes)

    raise ValueError(
        "Unsupported file type for text extraction."
    )