from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    value: Any = None
    source_text: str | None = None
    page_number: int | None = None


class LineItem(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    line_total: float | None = None
    source_text: str | None = None
    page_number: int | None = None


class ExtractedData(BaseModel):
    fields: dict[str, ExtractedField] = Field(default_factory=dict)
    line_items: list[LineItem] = Field(default_factory=list)