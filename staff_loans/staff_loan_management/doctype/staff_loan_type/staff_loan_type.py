# Copyright (c) 2024, VV System Developers LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StaffLoanType(Document):
	def validate(self):
		self.validate_accounts()

	def validate_accounts(self):
		for fieldname in [
			"payment_account",
			"loan_account",
		]:
			company = frappe.get_value("Account", self.get(fieldname), "company")

			if company and company != self.company:
				frappe.throw(
					_("Account {0} does not belong to company {1}").format(
						frappe.bold(self.get(fieldname)), frappe.bold(self.company)
					)
				)

		if self.get("loan_account") == self.get("payment_account"):
			frappe.throw(_("Loan Account and Payment Account cannot be same"))

@frappe.whitelist()
def get_mode_of_payment_account(company,mode_of_payment):
	doc = frappe.get_doc("Mode of Payment",mode_of_payment)
	if len(doc.accounts) > 0:
		for row in doc.accounts:
			if row.company == company and row.default_account:
				return row.default_account