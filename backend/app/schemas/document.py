from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FileValidation(BaseModel):
    is_valid: bool
    file_type: str | None = None
    file_size_bytes: int | None = None
    page_count: int | None = None
    errors: list[str] = Field(default_factory=list)


class ValidationCheck(BaseModel):
    name: str
    formula: str
    operands: dict[str, Any] = Field(default_factory=dict)
    calculated_value: float | None = None
    reported_value: float | None = None
    variance: float | None = None
    status: str


class ValidationResult(BaseModel):
    checks: list[ValidationCheck] = Field(default_factory=list)


class ProcessingMetadata(BaseModel):
    ocr_used: bool = False
    processed_at: datetime | None = None
    processing_time_ms: int | None = None


class DocumentResponse(BaseModel):
    document_name: str
    document_type: str
    processing_status: str
    overall_confidence: float | None = None

    file_validation: FileValidation
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    validation: ValidationResult
    processing_metadata: ProcessingMetadata