// Copyright (c) 2023, VV System Developers LTD and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Staff Loan Repayment and Closure"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "applicant",
			"label": __("Applicant"),
			"fieldtype": "Link",
			"options": "Employee",
		},
	]
};

