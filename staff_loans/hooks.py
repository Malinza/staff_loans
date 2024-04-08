from . import __version__ as app_version

app_name = "staff_loans"
app_title = "Staff Loans"
app_publisher = "VV System Developers LTD"
app_description = "An App that manages staff loans and loan rescheduling"
app_email = "ibrahim@vvsdtz.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/staff_loans/css/staff_loans.css"
# app_include_js = "/assets/staff_loans/js/staff_loans.js"

# include js, css files in header of web template
# web_include_css = "/assets/staff_loans/css/staff_loans.css"
# web_include_js = "/assets/staff_loans/js/staff_loans.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "staff_loans/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {
# 	"Loan Application" : "public/js/button.js"
# }
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "staff_loans.utils.jinja_methods",
#	"filters": "staff_loans.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "staff_loans.install.before_install"
# after_install = "staff_loans.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "staff_loans.uninstall.before_uninstall"
# after_uninstall = "staff_loans.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "staff_loans.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Journal Entry": {
		"on_submit": "staff_loans.custom.loan.on_submit",
	},
    "Payroll Entry": {
		"before_submit": "staff_loans.custom.loan.add_additional_salary"
	},
    "Additional Salary": {
		"before_cancel": "staff_loans.custom.loan.do_cancell",
	},
    "Salary Slip": {
		"on_submit": "staff_loans.custom.loan.on_salary_slip_submit",
        "before_save": "staff_loans.custom.loan.add_additional_salary_on_salary_slip",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"staff_loans.tasks.all"
#	],
#	"daily": [
#		"staff_loans.tasks.daily"
#	],
#	"hourly": [
#		"staff_loans.tasks.hourly"
#	],
#	"weekly": [
#		"staff_loans.tasks.weekly"
#	],
#	"monthly": [
#		"staff_loans.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "staff_loans.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "staff_loans.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "staff_loans.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"staff_loans.auth.validate"
# ]
