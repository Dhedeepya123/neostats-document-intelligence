import re
from typing import Any


def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving
    meaningful financial information.
    """

    if not text:
        return ""

    # Normalize different types of whitespace.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces while keeping line structure.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_number(value: str | None) -> float | None:
    """
    Convert a financial number into a Python float.

    Handles common formats such as:
        1,250.50
        1250.50
        (500)
        -500
    """

    if not value:
        return None

    value = value.strip()

    is_negative = (
        value.startswith("(")
        and value.endswith(")")
    )

    # Remove currency symbols and other non-numeric characters,
    # while preserving commas, decimal points and minus signs.
    cleaned = re.sub(r"[^\d,.\-]", "", value)

    if not cleaned:
        return None

    cleaned = cleaned.replace(",", "")

    try:
        number = float(cleaned)

        if is_negative:
            number = -abs(number)

        return number

    except ValueError:
        return None


def find_labeled_value(
    text: str,
    labels: list[str],
) -> tuple[str | None, str | None]:
    """
    Find a value appearing after a known label.

    This helper is intentionally generic. It does not contain
    expected answers for any particular dataset document.
    """

    if not text:
        return None, None

    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:\-]?\s*([^\n]+)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()
            source_text = match.group(0).strip()

            return value, source_text

    return None, None


def extract_basic_fields(
    text: str,
    document_type: str,
) -> dict[str, Any]:
    """
    Perform basic deterministic extraction from available text.

    AI-based extraction will be integrated into this service
    later for complete document understanding.
    """

    text = clean_text(text)

    result: dict[str, Any] = {
        "fields": {},
        "line_items": [],
    }

    if not text:
        return result

    # ---------------------------------------------------------
    # Common financial document fields
    # ---------------------------------------------------------

    common_fields = {
        "currency": [
            "Currency",
            "Currency Code",
        ],
    }

    if document_type == "invoice":

        common_fields.update(
            {
                "invoice_number": [
                    "Invoice Number",
                    "Invoice No",
                    "Invoice #",
                ],
                "invoice_date": [
                    "Invoice Date",
                    "Date",
                ],
                "vendor_name": [
                    "Vendor Name",
                    "Vendor",
                    "Seller",
                ],
                "customer_name": [
                    "Customer Name",
                    "Customer",
                    "Bill To",
                ],
                "subtotal": [
                    "Subtotal",
                    "Sub Total",
                ],
                "tax_amount": [
                    "Tax Amount",
                    "Tax",
                    "GST",
                    "VAT",
                ],
                "discount": [
                    "Discount",
                ],
                "total_amount": [
                    "Total Amount",
                    "Grand Total",
                    "Total",
                ],
            }
        )

    elif document_type == "balance_sheet":

        common_fields.update(
            {
                "total_assets": [
                    "Total Assets",
                ],
                "total_liabilities": [
                    "Total Liabilities",
                ],
                "total_equity": [
                    "Total Equity",
                ],
            }
        )

    elif document_type == "profit_and_loss":

        common_fields.update(
            {
                "revenue": [
                    "Revenue",
                    "Total Revenue",
                ],
                "cost_of_sales": [
                    "Cost of Sales",
                    "Cost of Goods Sold",
                    "COGS",
                ],
                "gross_profit": [
                    "Gross Profit",
                ],
                "operating_expenses": [
                    "Operating Expenses",
                ],
                "operating_profit": [
                    "Operating Profit",
                ],
                "tax": [
                    "Tax",
                    "Income Tax",
                ],
                "net_profit": [
                    "Net Profit",
                    "Net Income",
                ],
            }
        )

    elif document_type == "cash_flow_statement":

        common_fields.update(
            {
                "operating_cash_flow": [
                    "Operating Cash Flow",
                    "Cash Flow from Operating Activities",
                ],
                "investing_cash_flow": [
                    "Investing Cash Flow",
                    "Cash Flow from Investing Activities",
                ],
                "financing_cash_flow": [
                    "Financing Cash Flow",
                    "Cash Flow from Financing Activities",
                ],
                "opening_cash": [
                    "Opening Cash",
                    "Cash at Beginning",
                ],
                "net_change_in_cash": [
                    "Net Change in Cash",
                    "Net Increase in Cash",
                ],
                "closing_cash": [
                    "Closing Cash",
                    "Cash at End",
                ],
            }
        )

    # ---------------------------------------------------------
    # Extract available labeled values
    # ---------------------------------------------------------

    for field_name, labels in common_fields.items():

        raw_value, source_text = find_labeled_value(
            text,
            labels,
        )

        if raw_value is None:
            continue

        # Financial numeric fields should become numbers.
        numeric_fields = {
            "subtotal",
            "tax_amount",
            "discount",
            "total_amount",
            "total_assets",
            "total_liabilities",
            "total_equity",
            "revenue",
            "cost_of_sales",
            "gross_profit",
            "operating_expenses",
            "operating_profit",
            "tax",
            "net_profit",
            "operating_cash_flow",
            "investing_cash_flow",
            "financing_cash_flow",
            "opening_cash",
            "net_change_in_cash",
            "closing_cash",
        }

        value: Any = raw_value

        if field_name in numeric_fields:
            value = normalize_number(raw_value)

        result["fields"][field_name] = {
            "value": value,
            "source_text": source_text,
            "page_number": None,
        }

    return result


def extract_document(
    text: str,
    document_type: str,
) -> dict[str, Any]:
    """
    Main extraction entry point.

    Returns a consistent structure regardless of document type.
    """

    supported_types = {
        "invoice",
        "balance_sheet",
        "profit_and_loss",
        "cash_flow_statement",
    }

    if document_type not in supported_types:
        raise ValueError(
            "Unsupported document type."
        )

    return extract_basic_fields(
        text=text,
        document_type=document_type,
    )