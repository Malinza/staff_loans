# Copyright (c) 2023, VV System Developers LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	# chart_data = get_chart_data(data)
	return columns, data, None,None #chart_data

def get_columns(filters):
	return [
		{"fieldname": "applicant", "fieldtype": "Data", "label": _("Applicant"), "width": "150px"},
		{"fieldname": "applicant_name", "fieldtype": "Data", "label": _("Applicant Name"), "width": "150px"},
		{"fieldname": "loan", "fieldtype": "Data", "label": _("Loan"), "width": "100px"},
		{"fieldname": "total_payable_amount", "fieldtype": "Currency", "label": _("Total Payable Amount"), "width": "150px"},
		{"fieldname": "amount_paid_from_salary", "fieldtype": "Currency", "label": _("Amount Paid From Salary"), "width": "150px"},
		{"fieldname": "amount_paid_not_from_salary", "fieldtype": "Currency", "label": _("Amount Paid not From Salary"), "width": "150px"},
		{"fieldname": "write_off_amount", "fieldtype": "Currency", "label": _("Write Off Amount"), "width": "150px"},
		{"fieldname": "loan_balance", "fieldtype": "Currency", "label": _("Loan Balance"), "width": "150px"},
	]


@frappe.whitelist()
def get_data(filters):
	loans = frappe.db.sql(f"""
			SELECT
			l.applicant AS applicant, 
			l.applicant_name AS applicant_name,
			l.name AS loan,
			l.loan_amount AS total_payable_amount,
			l.written_off_amount AS write_off_amount,
			0 AS amount_paid_from_salary,
			(SELECT SUM(ls.total_payment) FROM `tabStaff Loan` l
			INNER JOIN `tabStaff Loan Repayment Schedule` ls ON l.name = ls.parent AND ls.parentfield = 'repayment_schedule'
			LEFT JOIN `tabStaff Loan Repayment` lr ON ls.repayment_reference = lr.name
			WHERE l.name = '{filters.employee}'
			AND l.docstatus = 1
			AND lr.repayment_type = 'External Sources') AS amount_paid_not_from_salary,
			null AS loan_balance
		FROM `tabStaff Loan` l 
		INNER JOIN `tabStaff Loan Repayment Schedule` ls ON l.name = ls.parent AND ls.parentfield = 'repayment_schedule'
		WHERE l.name = '{filters.emloyee}'
		AND l.docstatus = 1
		AND ls.repayment_reference = ''
		AND ls.outsource = 0
		AND l.status = "Disbursed"
		""", as_dict=1)
	return loans