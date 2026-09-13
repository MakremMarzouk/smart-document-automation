from decimal import Decimal
from typing import Any


class InvoiceValidator:
    @staticmethod
    def validate(invoice_data: dict[str, Any]) -> list[str]:
        errors: list[str] = []

        required_fields = [
            "invoice_number",
            "vendor_name",
            "invoice_date",
            "total_amount",
        ]

        for field in required_fields:
            value = invoice_data.get(field)

            if value is None or value == "":
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        total_amount = Decimal(str(invoice_data["total_amount"]))

        if total_amount <= 0:
            errors.append("Total amount must be greater than zero")

        items = invoice_data.get("items", [])
        subtotal_value = invoice_data.get("subtotal") or 0
        subtotal = Decimal(str(subtotal_value))

        calculated_subtotal = Decimal("0")

        for item in items:
            quantity = Decimal(str(item.get("quantity") or 0))
            unit_price = Decimal(str(item.get("unit_price") or 0))

            calculated_subtotal += quantity * unit_price

        if abs(calculated_subtotal - subtotal) > Decimal("0.01"):
            errors.append(
                "Items total does not match the subtotal"
            )

        tax_value = invoice_data.get("tax_amount") or 0
        tax_amount = Decimal(str(tax_value))

        if abs((subtotal + tax_amount) - total_amount) > Decimal("0.01"):
            errors.append(
                "Subtotal plus tax does not match the total amount"
            )

        invoice_date = invoice_data.get("invoice_date")
        due_date = invoice_data.get("due_date")

        if due_date and invoice_date and due_date < invoice_date:
            errors.append(
                "Due date cannot be earlier than invoice date"
            )

        return errors