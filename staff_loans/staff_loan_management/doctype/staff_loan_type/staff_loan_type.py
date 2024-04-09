# Copyright (c) 2024, VV System Developers LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StaffLoanType(Document):
	pass

@frappe.whitelist()
def get_mode_of_payment_account(company,mode_of_payment):
	doc = frappe.get_doc("Mode of Payment",mode_of_payment)
	if len(doc.accounts) > 0:
		for row in doc.accounts:
			if row.company == company and row.default_account:
				return row.default_account