{% include 'erpnext/loan_management/loan_common.js' %};

frappe.ui.form.on('Loan Application', {

	add_toolbar_buttons: function(frm) {
		if (frm.doc.status == "Approved" && frm.doc.docstatus == 1) {
			frappe.db.get_value("Staff Loan", {"loan_application": frm.doc.name, "docstatus": 1}, "name", (r) => {
					frm.add_custom_button(__('Staff Loans'), function() {
						frm.trigger('create_loans');
					},__('Create'))
			});
		}
	},
	create_loans: function(frm) {
		if (frm.doc.status != "Approved") {
			frappe.throw(__("Cannot create loan until application is approved"));
		}

		frappe.model.open_mapped_doc({
			method: 'staff_loans.Custom.button_method.create_loans',
			frm: frm
		});
	}
});