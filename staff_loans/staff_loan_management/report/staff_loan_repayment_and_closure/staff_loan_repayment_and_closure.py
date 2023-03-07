# Copyright (c) 2023, VV System Developers LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Posting Date"), "fieldtype": "Date", "fieldname": "posting_date", "width": 100},
		{
			"label": _("Loan Repayment"),
			"fieldtype": "Link",
			"fieldname": "loan_repayment",
			"options": "Staff Loan Repayment",
			"width": 100,
		},
		{
			"label": _("Loan"),
			"fieldtype": "Link",
			"fieldname": "loan",
			"options": "Staff Loan",
			"width": 200,
		},
		{"label": _("Applicant"), "fieldtype": "Data", "fieldname": "applicant", "width": 150},
		{"label": _("Payment Type"), "fieldtype": "Data", "fieldname": "repayment_type", "width": 150},
		{
			"label": _("Paid Amount"),
			"fieldtype": "Currency",
			"fieldname": "paid_amount",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Currency"),
			"fieldtype": "Link",
			"fieldname": "currency",
			"options": "Currency",
			"width": 100,
		},
	]


def get_data(filters):
	data = []

	query_filters = {
		"docstatus": 1,
		"company": filters.get("company"),
	}

	if filters.get("applicant"):
		query_filters.update({"applicant": filters.get("applicant")})

	loan_repayments = frappe.get_all(
		"Staff Loan Repayment",
		filters=query_filters,
		fields=[
			"payment_date",
			"applicant",
			"name",
			"loan",
			"repayment_amount",
			"repayment_type",
		],
	)

	default_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency")

	for repayment in loan_repayments:
		row = {
			"posting_date": repayment.payment_date,
			"loan_repayment": repayment.name,
			"applicant": repayment.applicant,
			"repayment_type": repayment.repayment_type,
			"loan": repayment.loan,
			"paid_amount": repayment.repayment_amount,
			"currency": default_currency,
		}

		data.append(row)

	return data

