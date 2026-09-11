from app.schemas.extraction import ExtractedData


def test_extracted_data_structure():
    data = ExtractedData(
        fields={
            "invoice_number": {
                "value": "INV-001",
                "source_text": "Invoice No: INV-001",
                "page_number": 1,
            },
            "total_amount": {
                "value": 1180,
                "source_text": "Total: 1180",
                "page_number": 1,
            },
        },
        line_items=[],
    )

    assert "invoice_number" in data.fields
    assert data.fields["invoice_number"].value == "INV-001"
    assert data.fields["invoice_number"].page_number == 1
    assert data.fields["total_amount"].value == 1180


def test_line_item_structure():
    data = ExtractedData(
        fields={},
        line_items=[
            {
                "description": "Laptop",
                "quantity": 2,
                "unit_price": 500,
                "line_total": 1000,
                "source_text": "Laptop 2 x 500 = 1000",
                "page_number": 1,
            }
        ],
    )

    assert len(data.line_items) == 1
    assert data.line_items[0].description == "Laptop"
    assert data.line_items[0].quantity == 2
    assert data.line_items[0].unit_price == 500
    assert data.line_items[0].line_total == 1000


def test_missing_values_are_allowed():
    data = ExtractedData(
        fields={
            "tax_amount": {
                "value": None,
                "source_text": None,
                "page_number": None,
            }
        },
        line_items=[],
    )

    assert data.fields["tax_amount"].value is None
    assert data.fields["tax_amount"].source_text is None
    assert data.fields["tax_amount"].page_number is None
