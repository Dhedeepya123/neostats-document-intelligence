import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.document_repository import create_document
from app.services.ai_extraction_service import extract_with_gemini
from app.services.document_validation_service import validate_document
from app.services.financial_validation_service import validate_financial_data


def normalize_document_type(document_type: str) -> str:
    value = document_type.strip().lower()

    mapping = {
        "invoice": "invoice",
        "balance sheet": "balance_sheet",
        "balance_sheet": "balance_sheet",
        "profit & loss": "profit_and_loss",
        "profit and loss": "profit_and_loss",
        "profit_and_loss": "profit_and_loss",
        "cash flow": "cash_flow_statement",
        "cash flow statement": "cash_flow_statement",
        "cash_flow": "cash_flow_statement",
        "cash_flow_statement": "cash_flow_statement",
    }

    if value not in mapping:
        raise ValueError(
            f"Unsupported document type: {document_type}"
        )

    return mapping[value]


def process_document(
    db: Session,
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
    document_type: str,
) -> dict:
    start_time = time.perf_counter()

    normalized_type = normalize_document_type(
        document_type
    )

    # ---------------------------------------------------------
    # STEP 1: FILE VALIDATION
    # ---------------------------------------------------------

    file_validation = validate_document(
        filename=filename,
        content_type=content_type,
        file_bytes=file_bytes,
        max_file_size_mb=10,
        max_pages=3,
    )

    file_validation_data = file_validation.to_dict()

    if not file_validation_data["is_valid"]:
        processing_time_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        processing_metadata = {
            "ocr_used": False,
            "processed_at": (
                datetime.now(timezone.utc).isoformat()
            ),
            "processing_time_ms": processing_time_ms,
        }

        result = {
            "document_name": filename,
            "document_type": normalized_type,
            "processing_status": "FAILED",
            "overall_confidence": None,
            "file_validation": file_validation_data,
            "extracted_data": {
                "fields": {},
                "line_items": [],
            },
            "validation": {
                "checks": []
            },
            "processing_metadata": processing_metadata,
        }

        create_document(
            db=db,
            document_name=filename,
            document_type=normalized_type,
            processing_status="FAILED",
            file_validation=file_validation_data,
            extracted_data=result["extracted_data"],
            validation=result["validation"],
            processing_metadata=processing_metadata,
            overall_confidence=None,
        )

        return result

    # ---------------------------------------------------------
    # STEP 2: AI EXTRACTION FROM ORIGINAL DOCUMENT
    # ---------------------------------------------------------

    extracted_data = extract_with_gemini(
        document_type=normalized_type,
        file_bytes=file_bytes,
        file_type=file_validation_data["file_type"],
    )

    if not isinstance(extracted_data, dict):
        extracted_data = {}

    extracted_data.setdefault(
        "fields",
        {}
    )

    extracted_data.setdefault(
        "line_items",
        []
    )

    # ---------------------------------------------------------
    # STEP 3: FINANCIAL VALIDATION
    # ---------------------------------------------------------

    validation = validate_financial_data(
        document_type=normalized_type,
        extracted_data=extracted_data,
        tolerance=0.01,
    )

    # ---------------------------------------------------------
    # STEP 4: PROCESSING METADATA
    # ---------------------------------------------------------

    processing_time_ms = int(
        (time.perf_counter() - start_time) * 1000
    )

    processing_metadata = {
        "ocr_used": False,
        "processed_at": (
            datetime.now(timezone.utc).isoformat()
        ),
        "processing_time_ms": processing_time_ms,
    }

    # ---------------------------------------------------------
    # STEP 5: FINAL RESULT
    # ---------------------------------------------------------

    result = {
        "document_name": filename,
        "document_type": normalized_type,
        "processing_status": "PASS",
        "overall_confidence": None,
        "file_validation": file_validation_data,
        "extracted_data": extracted_data,
        "validation": validation,
        "processing_metadata": processing_metadata,
    }

    # ---------------------------------------------------------
    # STEP 6: SAVE TO DATABASE
    # ---------------------------------------------------------

    create_document(
        db=db,
        document_name=filename,
        document_type=normalized_type,
        processing_status="PASS",
        file_validation=file_validation_data,
        extracted_data=extracted_data,
        validation=validation,
        processing_metadata=processing_metadata,
        overall_confidence=None,
    )

    return result