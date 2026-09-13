from app.services.validator import InvoiceValidator


def test_valid_invoice_returns_no_errors():
    invoice = {
        "invoice_number": "INV-1",
        "vendor_name": "Test Vendor",
        "invoice_date": "2026-09-13",
        "due_date": "2026-09-20",
        "items": [
            {
                "description": "Service",
                "quantity": 2,
                "unit_price": 50,
            }
        ],
        "subtotal": 100,
        "tax_amount": 10,
        "total_amount": 110,
    }

    errors = InvoiceValidator.validate(invoice)

    assert errors == []


def test_missing_required_fields():
    invoice = {
        "vendor_name": "Test Vendor",
        "total_amount": 100,
    }

    errors = InvoiceValidator.validate(invoice)

    assert "Missing required field: invoice_number" in errors
    assert "Missing required field: invoice_date" in errors


def test_total_must_be_positive():
    invoice = {
        "invoice_number": "INV-2",
        "vendor_name": "Test Vendor",
        "invoice_date": "2026-09-13",
        "subtotal": 0,
        "tax_amount": 0,
        "total_amount": 0,
    }

    errors = InvoiceValidator.validate(invoice)

    assert "Total amount must be greater than zero" in errors


def test_subtotal_and_tax_must_match_total():
    invoice = {
        "invoice_number": "INV-3",
        "vendor_name": "Test Vendor",
        "invoice_date": "2026-09-13",
        "subtotal": 100,
        "tax_amount": 10,
        "total_amount": 50,
    }

    errors = InvoiceValidator.validate(invoice)

    assert "Subtotal plus tax does not match the total amount" in errors


def test_due_date_cannot_be_before_invoice_date():
    invoice = {
        "invoice_number": "INV-4",
        "vendor_name": "Test Vendor",
        "invoice_date": "2026-09-20",
        "due_date": "2026-09-13",
        "subtotal": 100,
        "tax_amount": 0,
        "total_amount": 100,
    }

    errors = InvoiceValidator.validate(invoice)

    assert "Due date cannot be earlier than invoice date" in errors

def test_items_must_match_subtotal():
    invoice = {
        "invoice_number": "INV-5",
        "vendor_name": "Test Vendor",
        "invoice_date": "2026-09-13",
        "items": [
            {
                "description": "Service",
                "quantity": 2,
                "unit_price": 50,
            }
        ],
        "subtotal": 150,
        "tax_amount": 0,
        "total_amount": 150,
    }

    errors = InvoiceValidator.validate(invoice)

    assert "Items total does not match the subtotal" in errors