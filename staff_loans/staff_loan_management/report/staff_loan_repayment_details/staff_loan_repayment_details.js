// Copyright (c) 2023, VV System Developers LTD and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Staff Loan Repayment Details"] = {
	"filters": [
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": __("Employee"),
			"options": "Employee",
			"reqd": 1
		}
	]
};
