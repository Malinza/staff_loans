# Copyright (c) 2023, VV System Developers LTD and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class StaffLoanSettings(Document):
	def before_save(self):
		if self.enable_multi_company:
			self.credit_account = ""
			self.salary_component = ""
			self.debit_account = ""
			self.jv_posting_date_based_on = ""
