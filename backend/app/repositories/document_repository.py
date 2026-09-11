import json

from sqlalchemy.orm import Session

from app.models.document import Document


def create_document(
    db: Session,
    document_name: str,
    document_type: str,
    processing_status: str,
    file_validation: dict,
    extracted_data: dict,
    validation: dict,
    processing_metadata: dict,
    overall_confidence: float | None = None,
) -> Document:
    """
    Create and save a processed document in the database.
    """

    document = Document(
        document_name=document_name,
        document_type=document_type,
        processing_status=processing_status,
        file_validation=json.dumps(file_validation),
        extracted_data=json.dumps(extracted_data),
        validation=json.dumps(validation),
        processing_metadata=json.dumps(processing_metadata),
        overall_confidence=overall_confidence,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_latest_document_by_name(
    db: Session,
    document_name: str,
) -> Document | None:
    """
    Retrieve the latest processed version of a document
    using its filename.
    """

    return (
        db.query(Document)
        .filter(
            Document.document_name == document_name
        )
        .order_by(
            Document.created_at.desc()
        )
        .first()
    )


def get_all_documents(
    db: Session,
) -> list[Document]:
    """
    Retrieve all processed documents.

    Newest documents are returned first.
    """

    return (
        db.query(Document)
        .order_by(
            Document.created_at.desc()
        )
        .all()
    )


def document_to_dict(
    document: Document,
) -> dict:
    """
    Convert a database Document object back into
    the structured API response format.
    """

    return {
        "document_name": document.document_name,
        "document_type": document.document_type,
        "processing_status": document.processing_status,
        "overall_confidence": document.overall_confidence,
        "file_validation": json.loads(
            document.file_validation
        )
        if document.file_validation
        else {},
        "extracted_data": json.loads(
            document.extracted_data
        )
        if document.extracted_data
        else {},
        "validation": json.loads(
            document.validation
        )
        if document.validation
        else {"checks": []},
        "processing_metadata": json.loads(
            document.processing_metadata
        )
        if document.processing_metadata
        else {},
    }