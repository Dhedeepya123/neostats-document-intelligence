from app.services.financial_validation_service import validate_financial_data


def test_invoice_total_validation():
    extracted_data = {
        "fields": {
            "subtotal": {"value": 1000},
            "tax_amount": {"value": 180},
            "discount": {"value": 0},
            "total_amount": {"value": 1180},
        },
        "line_items": [],
    }

    result = validate_financial_data(
        document_type="invoice",
        extracted_data=extracted_data,
        tolerance=0.01,
    )

    checks = result["checks"]

    total_check = next(
        check
        for check in checks
        if check["name"] == "Invoice: Subtotal plus tax less discount"
    )

    assert total_check["status"] == "PASS"
    assert total_check["calculated_value"] == 1180
    assert total_check["reported_value"] == 1180
    assert total_check["variance"] == 0.0


def test_invoice_total_failure():
    extracted_data = {
        "fields": {
            "subtotal": {"value": 1000},
            "tax_amount": {"value": 180},
            "discount": {"value": 0},
            "total_amount": {"value": 1200},
        },
        "line_items": [],
    }

    result = validate_financial_data(
        document_type="invoice",
        extracted_data=extracted_data,
        tolerance=0.01,
    )

    checks = result["checks"]

    total_check = next(
        check
        for check in checks
        if check["name"] == "Invoice: Subtotal plus tax less discount"
    )

    assert total_check["status"] == "FAIL"
    assert total_check["calculated_value"] == 1180
    assert total_check["reported_value"] == 1200
    assert total_check["variance"] == 20.0
