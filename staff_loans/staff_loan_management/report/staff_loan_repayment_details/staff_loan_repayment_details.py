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
	return columns, data, None

def get_columns():
	return [
		{"fieldname": "applicant", "fieldtype": "Data", "label": _("Applicant"), "width": "150px"},
		{"fieldname": "applicant_name", "fieldtype": "Data", "label": _("Applicant Name"), "width": "150px"},
		{"fieldname": "company", "fieldtype": "Data", "label": _("Company"), "width": "150px"},
		{"fieldname": "loan", "fieldtype": "Data", "label": _("Loan"), "width": "100px"},
		{"fieldname": "total_payable_amount", "fieldtype": "Currency", "label": _("Total Payable Amount"), "width": "150px"},
		{"fieldname": "amount_paid_from_salary", "fieldtype": "Currency", "label": _("Amount Paid From Salary"), "width": "150px"},
		{"fieldname": "amount_paid_not_from_salary", "fieldtype": "Currency", "label": _("Amount Paid not From Salary"), "width": "150px"},
		{"fieldname": "write_off_amount", "fieldtype": "Currency", "label": _("Write Off Amount"), "width": "150px"},
		{"fieldname": "loan_balance", "fieldtype": "Currency", "label": _("Loan Balance"), "width": "150px"},
	]


@frappe.whitelist()
def get_data(filters):
	if filters.get("employee"):
		employee_filter = f"AND l.applicant = '{filters.employee}'"
		employee_inner_join_filter = f"AND ln.applicant = '{filters.employee}'"
		employee_inner_join_filter2 = f"AND ll.applicant = '{filters.employee}'"
	else:
		employee_filter = ""
		employee_inner_join_filter = ""
		employee_inner_join_filter2 = ""

	if filters.get("company"):
		company_filter = f"AND l.company = '{filters.company}'"
		company_inner_join_filter = f"AND ln.company = '{filters.company}'"
		company_inner_join_filter2 = f"AND ll.company = '{filters.company}'"
	else:
		company_filter = ""
		company_inner_join_filter = ""
		company_inner_join_filter2 = ""

	loans = frappe.db.sql(f"""
		SELECT
			l.applicant AS applicant, 
			l.applicant_name AS applicant_name,
			l.company AS company,
			l.name AS loan,
			l.loan_amount AS total_payable_amount,
			l.written_off_amount AS write_off_amount,
			(
				SELECT SUM(lrs.total_payment) FROM `tabStaff Loan` ln
					INNER JOIN `tabStaff Loan Repayment Schedule` lrs ON ln.name = lrs.parent AND lrs.parentfield = 'repayment_schedule'
				WHERE ln.name = l.name
				AND lrs.outsource = 0
				AND lrs.repayment_reference IS NULL
				AND lrs.is_paid = 1
				AND ln.docstatus = 1
				{employee_inner_join_filter}
				{company_inner_join_filter}
				GROUP BY ln.name ORDER BY ln.name) AS amount_paid_from_salary,
			(
				SELECT SUM(lls.total_payment) FROM `tabStaff Loan` ll
					INNER JOIN `tabStaff Loan Repayment Schedule` lls ON ll.name = lls.parent AND lls.parentfield = 'repayment_schedule'
					LEFT JOIN `tabStaff Loan Repayment` llr ON lls.repayment_reference = llr.name
				WHERE ll.name = l.name
				AND ll.docstatus = 1
				{employee_inner_join_filter2}
				{company_inner_join_filter2}
				AND llr.repayment_type = 'External Sources' GROUP BY ll.name ORDER BY ll.name ASC) AS amount_paid_not_from_salary,
			SUM(l.loan_amount - l.total_amount_paid) AS loan_balance
		FROM `tabStaff Loan` l 
		WHERE l.docstatus = 1
		AND l.status = "Disbursed" 
		{employee_filter}
		{company_filter}
		GROUP BY l.name ORDER BY loan,company ASC
		""", as_dict=1)
	return loans