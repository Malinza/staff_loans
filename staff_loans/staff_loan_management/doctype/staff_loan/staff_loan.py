# Copyright (c) 2023, VV Systems Developer and contributors
# For license information, please see license.txt


import json
import math

import frappe
from frappe import _
from frappe.utils import get_link_to_form
from frappe.utils import (
	add_days,
	add_months,
	date_diff,
	flt,
	get_last_day,
	get_first_day,
	getdate,
	now_datetime,
	nowdate,
)
import os
import erpnext
from erpnext.accounts.doctype.journal_entry.journal_entry import get_payment_entry
from erpnext.controllers.accounts_controller import AccountsController



class StaffLoan(AccountsController):
	def on_update(self):
		self.validate_accounts()
		self.validate_cost_center()
		# self.set_status_from_docstatus()

	def after_submit_on_update(self):
		self.set_status_from_docstatus(self)

	def validate(self):
		self.validate_loan_application()
		self.set_loan_amount()
		self.validate_loan_amount()
		self.set_missing_fields()
		self.validate_cost_center()
		self.validate_accounts()
		self.check_sanctioned_amount_limit()

		if self.is_term_loan:
			validate_repayment_method(
				self.repayment_method,
				self.loan_amount,
				self.monthly_repayment_amount,
				self.repayment_periods,
				self.is_term_loan,
			)
			self.make_repayment_schedule()
			self.set_repayment_period()

		self.calculate_totals()

	def validate_loan_application(self):
		if self.loan_application:
			status = frappe.db.get_value("Loan Application",self.loan_application,"status")
			docstatus = frappe.db.get_value("Loan Application",self.loan_application,"docstatus")
			if docstatus != 1 or status != "Approved": 
				frappe.throw("Please Submit or Approve Loan Application before referencing it")
	
	def validate_accounts(self):
		for fieldname in [
			"payment_account",
			"loan_account",
			"interest_income_account",
			"penalty_income_account",
		]:
			company = frappe.get_value("Account", self.get(fieldname), "company")

			if company != self.company:
				frappe.throw(
					_("Account {0} does not belongs to company {1}").format(
						frappe.bold(self.get(fieldname)), frappe.bold(self.company)
					)
				)

	def validate_cost_center(self):
		if not self.cost_center and self.rate_of_interest != 0.0:
			self.cost_center = frappe.db.get_value("Company", self.company, "cost_center")

			if not self.cost_center:
				frappe.throw(_("Cost center is mandatory for loans having rate of interest greater than 0"))

	# def on_submit(self):
		# self.link_loan_security_pledge()
		# Interest accrual for backdated term loans
		# self.accrue_loan_interest()

	def after_submit(self):
		self.set_status_from_docstatus()

	def on_cancel(self):
		self.before_cancel_document()
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry"]
		
	def before_cancel(self):
		if self.status == "Disbursed":
			frappe.throw("You can't Cancel a Disbursed Loan, Please Write Off the Loan")

	def before_cancel_document(self):
		connected_docs = frappe.get_list("Journal Entry", filters={"cheque_no": self.name},fields={"docstatus","name"})
			
		for doc in connected_docs:
			if doc.docstatus == 1:
				link = get_link_to_form("Journal Entry", doc.name)
				frappe.throw(_("You must cancel journal entry {0} before cancelling this document").format(link))
				
		connected_doc = frappe.get_list("Staff Loan Repayment", filters={"loan": self.name},fields={"docstatus","name"})

		for doc in connected_doc:
			if doc.docstatus == 1:
				link = get_link_to_form("Staff Loan Repayment", doc.name)
				frappe.throw(_("You must cancel connected repayment entries {0} before cancelling this document").format(link))

	# frappe.db.after_cancel("Payment Entry", cancel_linked_journal_entry)

	def set_status_from_docstatus(self):
		self.status = self.docstatus

	def set_missing_fields(self):
		if not self.company:
			self.company = erpnext.get_default_company()

		if not self.posting_date:
			self.posting_date = nowdate()

		if self.loan_type and not self.rate_of_interest:
			self.rate_of_interest = frappe.db.get_value("Staff Loan Type", self.loan_type, "rate_of_interest")

		if self.repayment_method == "Repay Over Number of Periods":
			self.monthly_repayment_amount = get_monthly_repayment_amount(
				self.loan_amount, self.rate_of_interest, self.repayment_periods
			)

	def check_sanctioned_amount_limit(self):
		sanctioned_amount_limit = get_sanctioned_amount_limit(
			self.applicant_type, self.applicant, self.company
		)
		if sanctioned_amount_limit:
			total_loan_amount = get_total_loan_amount(self.applicant_type, self.applicant, self.company)

		if sanctioned_amount_limit and flt(self.loan_amount) + flt(total_loan_amount) > flt(
			sanctioned_amount_limit
		):
			frappe.throw(
				_("Sanctioned Amount limit crossed for {0} {1}").format(
					self.applicant_type, frappe.bold(self.applicant)
				)
			)

	def make_repayment_schedule(self):
		if not self.repayment_start_date:
			frappe.throw(_("Repayment Start Date is mandatory for term loans"))

		schedule_type_details = frappe.db.get_value(
			"Staff Loan Type", self.loan_type, ["repayment_schedule_type", "repayment_date_on"], as_dict=1
		)

		self.repayment_schedule = []
		payment_date = get_first_day(self.repayment_start_date)
		balance_amount = self.loan_amount

		while balance_amount > 0:
			interest_amount, principal_amount, balance_amount, total_payment = self.get_amounts(
				payment_date,
				balance_amount,
				schedule_type_details.repayment_schedule_type,
				schedule_type_details.repayment_date_on,
			)

			if schedule_type_details.repayment_schedule_type == "Pro-rated calendar months":
				next_payment_date = get_last_day(payment_date)
				if schedule_type_details.repayment_date_on == "Start of the next month":
					next_payment_date = add_days(next_payment_date, 1)

				payment_date = next_payment_date

			self.add_repayment_schedule_row(
				payment_date, principal_amount, total_payment, balance_amount
			)

			if (
				schedule_type_details.repayment_schedule_type == "Monthly as per repayment start date"
				or schedule_type_details.repayment_date_on == "End of the current month"
			):
				next_payment_date = add_single_month(payment_date)
				payment_date = next_payment_date

	def get_amounts(self, payment_date, balance_amount, schedule_type, repayment_date_on):
		if schedule_type == "Monthly as per repayment start date":
			days = 1
			months = 12
		else:
			expected_payment_date = get_last_day(payment_date)
			if repayment_date_on == "Start of the next month":
				expected_payment_date = add_days(expected_payment_date, 1)

			if expected_payment_date == payment_date:
				# using 30 days for calculating interest for all full months
				days = 30
				months = 365
			else:
				days = date_diff(get_last_day(payment_date), payment_date)
				months = 365

		interest_amount = flt(balance_amount * flt(self.rate_of_interest) * days / (months * 100))
		principal_amount = self.monthly_repayment_amount - interest_amount
		balance_amount = flt(balance_amount + interest_amount - self.monthly_repayment_amount)
		if balance_amount < 0:
			principal_amount += balance_amount
			balance_amount = 0.0

		total_payment = principal_amount + interest_amount

		return interest_amount, principal_amount, balance_amount, total_payment

	def add_repayment_schedule_row(
		self, payment_date, principal_amount, total_payment, balance_loan_amount
	):
		self.append(
			"repayment_schedule",
			{
				"payment_date": payment_date,
				"principal_amount": principal_amount,
				"total_payment": total_payment,
				"balance_loan_amount": balance_loan_amount,
			},
		)

	def set_repayment_period(self):
		if self.repayment_method == "Repay Fixed Amount per Period":
			repayment_periods = len(self.repayment_schedule)

			self.repayment_periods = repayment_periods

	def calculate_totals(self):
		self.total_payment = 0
		self.total_interest_payable = 0
		self.total_amount_paid = 0

		if self.is_term_loan:
			for data in self.repayment_schedule:
				self.total_payment += data.total_payment
		else:
			self.total_payment = self.loan_amount

	def set_loan_amount(self):
		if self.loan_application and not self.loan_amount:
			self.loan_amount = frappe.db.get_value("Staff Loan Application", self.loan_application, "loan_amount")

	def validate_loan_amount(self):
		if self.maximum_loan_amount and self.loan_amount > self.maximum_loan_amount:
			msg = _("Loan amount cannot be greater than {0}").format(self.maximum_loan_amount)
			frappe.throw(msg)

		if not self.loan_amount:
			frappe.throw(_("Loan amount is mandatory"))

def update_total_amount_paid(doc):
	total_amount_paid = 0
	for data in doc.repayment_schedule:
		if data.paid:
			total_amount_paid += data.total_payment
	frappe.db.set_value("Staff Loan", doc.name, "total_amount_paid", total_amount_paid)


def get_total_loan_amount(applicant_type, applicant, company):
	pending_amount = 0
	loan_details = frappe.db.get_all(
		"Staff Loan",
		filters={
			"applicant_type": applicant_type,
			"company": company,
			"applicant": applicant,
			"docstatus": 1,
			"status": ("!=", "Closed"),
		},
		fields=[
			"status",
			"total_payment",
			"disbursed_amount",
			"total_interest_payable",
			"total_principal_paid",
			"written_off_amount",
		],
	)

	interest_amount = flt(
		frappe.db.get_value(
			"Loan Interest Accrual",
			{"applicant_type": applicant_type, "company": company, "applicant": applicant, "docstatus": 1},
			"sum(interest_amount - paid_interest_amount)",
		)
	)

	for loan in loan_details:
		if loan.status in ("Disbursed", "Loan Closure Requested"):
			pending_amount += (
				flt(loan.total_payment)
				- flt(loan.total_interest_payable)
				- flt(loan.total_principal_paid)
				- flt(loan.written_off_amount)
			)
		elif loan.status == "Partially Disbursed":
			pending_amount += (
				flt(loan.disbursed_amount)
				- flt(loan.total_interest_payable)
				- flt(loan.total_principal_paid)
				- flt(loan.written_off_amount)
			)
		elif loan.status == "Sanctioned":
			pending_amount += flt(loan.total_payment)

	pending_amount += interest_amount

	return pending_amount


def get_sanctioned_amount_limit(applicant_type, applicant, company):
	return frappe.db.get_value(
		"Sanctioned Loan Amount",
		{"applicant_type": applicant_type, "company": company, "applicant": applicant},
		"sanctioned_amount_limit",
	)

@frappe.whitelist()
def validate_repayment_method(
	repayment_method, loan_amount, monthly_repayment_amount, repayment_periods, is_term_loan
):

	if is_term_loan and not repayment_method:
		frappe.throw(_("Repayment Method is mandatory for term loans"))

	if repayment_method == "Repay Over Number of Periods" and not repayment_periods:
		frappe.throw(_("Please enter Repayment Periods"))

	if repayment_method == "Repay Fixed Amount per Period":
		if not monthly_repayment_amount:
			frappe.throw(_("Please enter repayment Amount"))
		if monthly_repayment_amount > loan_amount:
			frappe.throw(_("Monthly Repayment Amount cannot be greater than Loan Amount"))

@frappe.whitelist()
def get_monthly_repayment_amount(loan_amount, rate_of_interest, repayment_periods):
	if rate_of_interest:
		monthly_interest_rate = flt(rate_of_interest) / (12 * 100)
		monthly_repayment_amount = math.ceil(
			(loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** repayment_periods)
			/ ((1 + monthly_interest_rate) ** repayment_periods - 1)
		)
	else:
		repayment_periods = int(repayment_periods)
		monthly_repayment_amount = math.ceil(flt(loan_amount) / repayment_periods)
	return monthly_repayment_amount


@frappe.whitelist()
def request_loan_closure(loan,loan_amount, total_amount_paid):

	pending_amount = flt(loan_amount) - flt(total_amount_paid)

	if pending_amount > 0:
		frappe.throw(_("Cannot close loan as there is an outstanding of {0}").format(pending_amount))

	frappe.db.set_value("Staff Loan", loan, "status", "Loan Closure Requested")

@frappe.whitelist()
def get_loan_application(loan_application):
	loan = frappe.get_doc("Staff Loan Application", loan_application)
	if loan:
		return loan.as_dict()


@frappe.whitelist()
def close_unsecured_term_loan(loan):
	loan_details = frappe.db.get_value(
		"Staff Loan", {"name": loan}, ["status", "is_term_loan", "is_secured_loan"], as_dict=1
	)

	if (
		loan_details.status == "Loan Closure Requested"
		and loan_details.is_term_loan
		and not loan_details.is_secured_loan
	):
		frappe.db.set_value("Staff Loan", loan, "status", "Closed")
	else:
		frappe.throw(_("Cannot close this loan until full repayment"))


def close_loan(loan, total_amount_paid):
	frappe.db.set_value("Staff Loan", loan, "total_amount_paid", total_amount_paid)
	frappe.db.set_value("Staff Loan", loan, "status", "Closed")


@frappe.whitelist()
def make_loan_disbursement(loan, company, applicant_type, applicant, pending_amount=0, as_dict=0):
	disbursement_entry = frappe.new_doc("Loan Disbursement")
	disbursement_entry.against_loan = loan
	disbursement_entry.applicant_type = applicant_type
	disbursement_entry.applicant = applicant
	disbursement_entry.company = company
	disbursement_entry.disbursement_date = nowdate()
	disbursement_entry.posting_date = nowdate()

	disbursement_entry.disbursed_amount = pending_amount
	if as_dict:
		return disbursement_entry.as_dict()
	else:
		return disbursement_entry


@frappe.whitelist()
def make_repayment_entry(loan, applicant_type, applicant, loan_type, company, as_dict=0):
	repayment_entry = frappe.new_doc("Loan Repayment")
	repayment_entry.against_loan = loan
	repayment_entry.applicant_type = applicant_type
	repayment_entry.applicant = applicant
	repayment_entry.company = company
	repayment_entry.loan_type = loan_type
	repayment_entry.posting_date = nowdate()

	if as_dict:
		return repayment_entry.as_dict()
	else:
		return repayment_entry


@frappe.whitelist()
def make_loan_write_off(loan, company=None, posting_date=None, amount=0, as_dict=0):
	if not company:
		company = frappe.get_value("Staff Loan", loan, "company")

	if not posting_date:
		posting_date = frappe.get_value("Staff Loan", loan, "posting_date")

	amount = frappe.get_value("Staff Loan", loan, "loan_amount")
	amt = 0
	pending_amount = frappe.get_value("Staff Loan", loan, "total_amount_paid")

	amt = amount - pending_amount

	payment_date = getdate()

	# get default write off account from company master
	write_off_account = frappe.get_value("Company", company, "write_off_account")

	write_off = frappe.new_doc("Staff Loan Repayment")
	write_off.applicant = frappe.get_value("Staff Loan", loan, "applicant")
	write_off.loan = loan
	write_off.cheque_date = posting_date
	write_off.payment_date = payment_date
	write_off.repayment_type = "Loan Write Off"
	write_off.write_off = write_off_account
	write_off.write_off_amount = amt
	write_off.company = company
	write_off.save()

	if as_dict:
		return write_off.as_dict()
	else:
		return write_off

@frappe.whitelist()
def make_loan_write_off_by_external_sources_entry(loan, company=None, posting_date=None, amount=0, as_dict=0):
	if not company:
		company = frappe.get_value("Staff Loan", loan, "company")

	if not posting_date:
		posting_date = frappe.get_value("Staff Loan", loan, "posting_date")

	amount = frappe.get_value("Staff Loan", loan, "loan_amount")
	amt = 0
	pending_amount = frappe.get_value("Staff Loan", loan, "total_amount_paid")

	amt = amount - pending_amount

	payment_date = getdate()

	write_off_by_external_sources = frappe.new_doc("Staff Loan Repayment")
	write_off_by_external_sources.applicant = frappe.get_value("Staff Loan", loan, "applicant")
	write_off_by_external_sources.loan = loan
	write_off_by_external_sources.cheque_date = posting_date
	write_off_by_external_sources.payment_date = payment_date
	write_off_by_external_sources.repayment_type = "External Sources"
	write_off_by_external_sources.repayment_amount = amt
	write_off_by_external_sources.description = "Loan Repayment By External Sources i.e. Cash, Cheque, Bank Transfer, etc."
	write_off_by_external_sources.company = company

	if as_dict:
		return write_off_by_external_sources.as_dict()
	else:
		return write_off_by_external_sources

def add_single_month(date):
	if getdate(date) == get_last_day(date):
		return get_last_day(add_months(date, 1))
	else:
		return add_months(date, 1)

@frappe.whitelist()
def make_refund_jv(loan, amount=0, reference_number=None, reference_date=None, submit=0):
	loan_details = frappe.db.get_value(
		"Staff Loan",
		loan,
		[
			"applicant_type",
			"applicant",
			"loan_account",
			"payment_account",
			"posting_date",
			"company",
			"name",
			"total_payment",
			"total_principal_paid",
		],
		as_dict=1,
	)

	loan_details.doctype = "Staff Loan"
	loan_details[loan_details.applicant_type.lower()] = loan_details.applicant

	if not amount:
		amount = flt(loan_details.total_principal_paid - loan_details.total_payment)

		if amount < 0:
			frappe.throw(_("No excess amount pending for refund"))

	refund_jv = get_payment_entry(
		loan_details,
		{
			"party_type": loan_details.applicant_type,
			"party_account": loan_details.loan_account,
			"amount_field_party": "debit_in_account_currency",
			"amount_field_bank": "credit_in_account_currency",
			"amount": amount,
			"bank_account": loan_details.payment_account,
		},
	)

	if reference_number:
		refund_jv.cheque_no = reference_number

	if reference_date:
		refund_jv.cheque_date = reference_date

	if submit:
		refund_jv.submit()

	return refund_jv
