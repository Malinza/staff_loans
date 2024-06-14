// Copyright (c) 2023, VV System Developers LTD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Staff Loan Settings', {
	refresh: function(frm) {
		// frm.make_methods = {
		// 	'Update Staff Loan Schedule': function() { frm.trigger('update_loan_schedule') },
		// }
		frm.add_custom_button(__('Staff Loan Schedule'), function() {
			frm.trigger("update_loan_schedule");
		},__('Update'));
	},
	update_loan_schedule: function(frm) {
		frappe.call({
			method: "staff_loans.custom.loan.recalculate_staff_loan_repayments",
			// callback: function(r){
			// }
		});
	},
});
