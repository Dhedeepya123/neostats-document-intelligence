import base64
import json

from google import genai

from app.core.config import settings


MODEL_NAME = "gemini-3.6-flash"


def get_client():
    if not settings.ai_api_key:
        raise ValueError(
            "AI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=settings.ai_api_key
    )


def build_extraction_prompt(document_type: str) -> str:
    return f"""
You are an expert financial document extraction system.

The document type is: {document_type}

You are given the ORIGINAL DOCUMENT itself.
Visually inspect the supplied document carefully.

Extract ALL meaningful information that is actually
visible in the document.

STRICT RULES:

1. Never invent or guess information.
2. Never use a template or assumed value.
3. If a value is missing or unreadable, return null.
4. Extract the exact visible values from the document.
5. Extract ALL meaningful fields, not only predefined fields.
6. Extract ALL table rows and line items.
7. Preserve financial periods such as current year and previous year.
8. Preserve negative values exactly as represented.
9. Numeric values must be returned as numbers when clearly numeric.
10. Dates and timestamps should be preserved as visible strings.
11. Include source_text for every extracted value whenever possible.
12. Include page_number for every extracted value.
13. For invoices, extract every line item with:
    description, quantity, unit_price and line_total.
14. Extract invoice totals, taxes, discounts, rounding,
    payments, change, customer information, vendor information,
    invoice number and all other visible meaningful information.
15. For financial statements, extract all headings,
    sub-headings, line items, totals, subtotals and
    values for every visible period.
16. Do not calculate values that are not explicitly visible.
17. Do not replace missing information with zero.
18. A visible zero must be extracted as zero.
19. If the document contains OCR-like or distorted text,
    use the visual appearance of the document to determine
    the most accurate value.
20. Do not copy example values from this prompt.

The required JSON structure is provided separately
through the response schema.

Return ONLY the JSON object.
"""


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "value": {},
                    "source_text": {
                        "type": [
                            "string",
                            "null"
                        ]
                    },
                    "page_number": {
                        "type": [
                            "integer",
                            "null"
                        ]
                    }
                },
                "required": [
                    "value",
                    "source_text",
                    "page_number"
                ]
            }
        },
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": [
                            "string",
                            "null"
                        ]
                    },
                    "quantity": {
                        "type": [
                            "number",
                            "null"
                        ]
                    },
                    "unit_price": {
                        "type": [
                            "number",
                            "null"
                        ]
                    },
                    "line_total": {
                        "type": [
                            "number",
                            "null"
                        ]
                    },
                    "source_text": {
                        "type": [
                            "string",
                            "null"
                        ]
                    },
                    "page_number": {
                        "type": [
                            "integer",
                            "null"
                        ]
                    }
                },
                "required": [
                    "description",
                    "quantity",
                    "unit_price",
                    "line_total",
                    "source_text",
                    "page_number"
                ]
            }
        }
    },
    "required": [
        "fields",
        "line_items"
    ]
}


def extract_with_gemini(
    document_type: str,
    file_bytes: bytes,
    file_type: str,
):
    client = get_client()

    prompt = build_extraction_prompt(
        document_type
    )

    encoded_file = base64.b64encode(
        file_bytes
    ).decode("utf-8")

    if file_type == "image/jpeg":
        media_content = {
            "type": "image",
            "data": encoded_file,
            "mime_type": "image/jpeg",
        }

    elif file_type == "image/png":
        media_content = {
            "type": "image",
            "data": encoded_file,
            "mime_type": "image/png",
        }

    elif file_type == "application/pdf":
        media_content = {
            "type": "document",
            "data": encoded_file,
            "mime_type": "application/pdf",
        }

    else:
        raise ValueError(
            f"Unsupported file type for AI extraction: {file_type}"
        )

    response = client.interactions.create(
        model=MODEL_NAME,
        input=[
            {
                "type": "text",
                "text": prompt,
            },
            media_content,
        ],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": RESPONSE_SCHEMA,
        },
    )

    output_text = response.output_text

    if not output_text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    try:
        return json.loads(output_text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON."
        ) from exc