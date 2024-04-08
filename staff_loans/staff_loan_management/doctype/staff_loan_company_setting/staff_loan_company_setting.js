// Copyright (c) 2024, VV System Developers LTD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Staff Loan Company Setting', {
	refresh: function(frm) {
		frm.set_query("credit_account", function () {
			return {
				"filters": {
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
		frm.set_query("debit_account", function () {
			return {
				"filters": {
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
	},
	company: (frm) => {
		frm.doc.debit_account = ""
		frm.doc.credit_account = ""
		frm.refresh_fields("debit_account","credit_account");
		// frm.refresh_field("credit_account");
	}
});
