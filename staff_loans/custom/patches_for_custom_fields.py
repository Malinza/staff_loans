import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "Loan": [
            {
                "fieldname": "repay_from_salary",
                "label": "Repay From Salary",
                "fieldtype": "Check",
                "insert_after": "status",
                "default": 0,
            }
        ]
    }

    create_custom_fields(fields, update=True)