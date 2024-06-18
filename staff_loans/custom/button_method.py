import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def create_loans(source_name, target_doc=None, submit=0):
	def update_accounts(source_doc, target_doc, source_parent):
		account_details = frappe.get_all(
			"Staff Loan Type",
			fields=[
				"mode_of_payment",
				"payment_account",
				"loan_account",
			],
			filters={"name": source_doc.loan_type},
		)[0]

		target_doc.mode_of_payment = account_details.mode_of_payment
		target_doc.payment_account = account_details.payment_account
		target_doc.loan_account = account_details.loan_account
		target_doc.loan_application = source_name

	doclist = get_mapped_doc(
		"Staff Loan Application",
		source_name,
		{
			"Staff Loan Application": {
				"doctype": "Staff Loan",
				"validation": {"docstatus": ["=", 1]},
				"postprocess": update_accounts,
			}
		},
		target_doc,
	)

	if submit:
		doclist.submit()

	return doclist
