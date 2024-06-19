// Copyright (c) 2024, VV System Developers LTD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Staff Loan Type', {
	mode_of_payment: (frm) => {
		frm.doc.disbursement_account = "";
		frm.refresh_field("disbursement_account");
		frappe.call({
			args: {
				"company": frm.doc.company,
				"mode_of_payment": frm.doc.mode_of_payment
			},
			method: "staff_loans.staff_loan_management.doctype.staff_loan_type.staff_loan_type.get_mode_of_payment_account",
			callback: function(r) {
				if (r.message) {
					frm.doc.disbursement_account = r.message;
					frm.refresh_field("disbursement_account");
				}
			}
		});
	}
});
