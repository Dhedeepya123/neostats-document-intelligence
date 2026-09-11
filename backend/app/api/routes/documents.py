import urllib.parse

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.document_repository import (
    document_to_dict,
    get_all_documents,
    get_latest_document_by_name,
)
from app.services.document_service import process_document


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


SUPPORTED_DOCUMENT_TYPES = {
    "invoice",
    "balance_sheet",
    "profit_and_loss",
    "cash_flow_statement",
}


@router.post("/process")
async def process_document_endpoint(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload and process a PDF/JPG/PNG document.
    """

    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_DOCUMENT_TYPE",
                "message": (
                    "document_type must be one of: "
                    "invoice, balance_sheet, "
                    "profit_and_loss, "
                    "cash_flow_statement."
                ),
            },
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_FILENAME",
                "message": "Uploaded file must have a filename.",
            },
        )

    try:
        file_bytes = await file.read()

        result = process_document(
            db=db,
            filename=file.filename,
            content_type=file.content_type,
            file_bytes=file_bytes,
            document_type=document_type,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "message": str(exc),
            },
        )

    except Exception as exc:
        print(
            "DOCUMENT PROCESSING ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "DOCUMENT_PROCESSING_ERROR",
                "message": str(exc),
            },
        )


@router.get("/{document_name}")
def get_document_by_name(
    document_name: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve the latest processed result for a document name.
    """

    decoded_name = urllib.parse.unquote(
        document_name
    )

    document = get_latest_document_by_name(
        db=db,
        document_name=decoded_name,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": (
                    f"No processed document found "
                    f"with name '{decoded_name}'."
                ),
            },
        )

    return document_to_dict(document)


@router.get("")
def list_documents(
    db: Session = Depends(get_db),
):
    """
    Return all processed documents for the dashboard.
    """

    documents = get_all_documents(db)

    return {
        "documents": [
            document_to_dict(document)
            for document in documents
        ]
    }