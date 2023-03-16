import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import nowdate
from frappe.utils import (
    get_first_day,
)
from datetime import datetime
from frappe.utils import flt
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def on_salary_slip_submit(doc, method):
    for deduction in doc.deductions:
        if deduction.salary_component == "Staff Loan":
            staff_loans = get_staff_loans(doc.employee)
            for staff_loan in staff_loans:
                update_staff_loan_repayment_schedule(staff_loan.name, deduction.additional_salary)


def get_staff_loans(employee):
    staff_loans = frappe.get_all("Staff Loan", filters={
        "applicant": employee, 
        "status": "Disbursed"
    }, fields=["name"])
    return [frappe.get_doc("Staff Loan", loan.name) for loan in staff_loans]


def update_staff_loan_repayment_schedule(staff_loan_name, payment_reference):
    staff_loan = frappe.get_doc("Staff Loan", staff_loan_name)
    for repayment in staff_loan.repayment_schedule:
        if repayment.payment_reference == payment_reference:
            repayment.is_paid = 1
            repayment.save()
            staff_loan.total_amount_paid += repayment.total_payment
    staff_loan.save()

@frappe.whitelist()
def make_loan_disbursement_journal_entry(loan, company,applicant,debit_account,applicant_type,credit_account, ref_date, pending_amount, as_dict=0):
    disbursement_entry = frappe.new_doc("Journal Entry")
    disbursement_entry.voucher_type = "Journal Entry"
    disbursement_entry.company = company
    disbursement_entry.posting_date = nowdate()
    disbursement_entry.cheque_no = loan
    disbursement_entry.cheque_date = ref_date

    # create a new item in the table
    new_item = disbursement_entry.append('accounts', {})

    # set the values for the item
    new_item.account = debit_account
    new_item.party_type = applicant_type
    new_item.party = applicant
    new_item.debit_in_account_currency = pending_amount
    new_item.credit_in_account_currency = 0

    disbursement_entry.append("accounts", {
        "account": credit_account,
        "debit_in_account_currency": 0,
        "credit_in_account_currency": pending_amount
    })
    
    disbursement_entry.disbursed_amount = pending_amount
    disbursement_entry.insert()
    if as_dict:
        return disbursement_entry.as_dict()
    else:
        return disbursement_entry

@frappe.whitelist()
def on_submit(doc, method):
    if frappe.db.exists ("Staff Loan", doc.cheque_no):
        cs_loan = frappe.get_doc("Staff Loan", doc.cheque_no)
        if cs_loan.loan_amount == doc.total_debit:
            cs_loan.status = "Disbursed"
            cs_loan.disbursement_date = doc.posting_date
            cs_loan.disbursed_amount = doc.total_debit
            cs_loan.save()
        else:
            frappe.throw("Disbursed amount is not equal to loan amount")

@frappe.whitelist()
def add_additional_salary(doc, method):

    # Check if the "Staff Loan" Salary Component exists
    if not frappe.db.exists("Salary Component", "Staff Loan"):
        frappe.throw("Staff Loan Salary Component does not exist")
        # Check if the document is being submitted
    for i in doc.employees:
            # Check if the "Staff Loan" document already exists
        if frappe.db.exists("Staff Loan", {"applicant": i.employee, "status": "Disbursed"}):
                # If it does, get the document
            # frappe.msgprint("Staff Loan document found {0}". format(i.employee))
            staff_loan_list = frappe.get_list("Staff Loan", filters={
                "applicant": i.employee, 
                "status": "Disbursed"
                },fields={"name"})
            for loans in staff_loan_list:
                # Get Repayment Schedule Amount
                new_checkk = datetime.strptime(doc.start_date, "%Y-%m-%d").date()
                # frappe.msgprint("Date is {0}". format(new_checkk))
                new_check = new_checkk.replace(day=1)
                repayment_amount = 0
                staff_loan = frappe.get_doc("Staff Loan", loans)
                for d in staff_loan.repayment_schedule:
                    # frappe.msgprint("Payment Date {0}". format(d.payment_date))
                    if d.payment_date == new_check and d.total_payment > 0 and d.is_paid == 0:
                        repayment_amount = d.total_payment
                        # if not frappe.db.exists("Additional Salary", {"employee": i.employee, "salary_component": staff_loan_component.name, "payroll_date": new_check, "docstatus": 1, "amount": repayment_amount}): 
                        if not d.payment_reference:
                            # If it doesn't exist, create a new Additional Salary
                            new_additional_salary = frappe.new_doc("Additional Salary")
                            new_additional_salary.employee = i.employee
                            new_additional_salary.employee_name = i.employee_name
                            new_additional_salary.company = doc.company
                            new_additional_salary.salary_component = "Staff Loan"
                            new_additional_salary.amount = repayment_amount
                            new_additional_salary.payroll_date = doc.start_date
                            new_additional_salary.insert()
                            new_additional_salary.submit()
                            d.payment_reference = new_additional_salary.name
                            d.save()

@frappe.whitelist()
def add_additional_salary_on_salary_slip(doc, method):

    # Check if the "Staff Loan" Salary Component exists
    if not frappe.db.exists("Salary Component", "Staff Loan"):
        frappe.throw("Staff Loan Salary Component does not exist")
        
    # Check if the "Staff Loan" document already exists
    if frappe.db.exists("Staff Loan", {"applicant": doc.employee, "status": "Disbursed"}):
        staff_loan_list = frappe.get_list("Staff Loan", filters={
            "applicant": doc.employee, 
            "status": "Disbursed"
            },fields={"name"})
        for loans in staff_loan_list:
            # Get Repayment Schedule Amount
            document_date = get_first_day(doc.start_date)
            # frappe.msgprint("Date is {0}". format(new_checkk))
            # new_check = new_checkk.replace(day=1)
            repayment_amount = 0
            staff_loan = frappe.get_doc("Staff Loan", loans)
            for d in staff_loan.repayment_schedule:
                # frappe.msgprint("Payment Date {0}". format(d.payment_date))
                if d.payment_date == document_date and d.total_payment > 0 and d.is_paid == 0:
                    repayment_amount = d.total_payment
                    # if not frappe.db.exists("Additional Salary", {"employee": doc.employee, "salary_component": staff_loan_component.name, "payroll_date": new_check, "docstatus": 1, "amount": repayment_amount}): 
                    if not d.payment_reference:
                        # If it doesn't exist, create a new Additional Salary
                        new_additional_salary = frappe.new_doc("Additional Salary")
                        new_additional_salary.employee = doc.employee
                        new_additional_salary.employee_name = doc.employee_name
                        new_additional_salary.company = doc.company
                        new_additional_salary.salary_component = "Staff Loan"
                        new_additional_salary.amount = repayment_amount
                        new_additional_salary.payroll_date = doc.start_date
                        new_additional_salary.insert()
                        new_additional_salary.submit()
                        d.payment_reference = new_additional_salary.name
                        d.save()

@frappe.whitelist()
def do_cancel(doc, method):
    # doc.ignore_linked_doctypes = ("Staff Loan")
    for i in doc.employees:
        if frappe.db.exists("Additional Salary", {"employee": i.employee, "salary_component": "Staff Loan", "payroll_date": doc.start_date, "docstatus": 1}):
            add_salary = frappe.get_list("Additional Salary", filters={
                    "employee": i.employee,
                    "salary_component": "Staff Loan",
                    "payroll_date": doc.start_date,
                    "docstatus": 1
                }, fields={"name"})
            for add in add_salary:
                if frappe.db.exists("Staff Loan", {"applicant": i.employee, "status": "Disbursed"}):
                    staff_loan = frappe.get_list("Staff Loan", filters={
                            "applicant": i.employee, 
                            "status": "Disbursed"
                            },fields={"name"})
                    for loans in staff_loan:
                        staff_loann = frappe.get_doc("Staff Loan", loans)
                        for d in staff_loann.repayment_schedule:
                            if d.payment_reference == add:
                                d.payment_reference = ""
                                d.is_paid = 0
                                d.save()
                additional_salary = frappe.get_doc("Additional Salary", add)
                additional_salary.cancel()
                additional_salary.delete()

@frappe.whitelist()
def do_cancell(doc, method):
    if frappe.db.exists("Staff Loan", {"status": "Disbursed"}):
        staff_loans = frappe.get_all("Staff Loan", filters={
            "status": "Disbursed"
        }, fields=["name"])
        for staff_loan in staff_loans:
            repayment_schedules = frappe.get_list("Staff Loan Repayment Schedule", filters={
                "parent": staff_loan.name,
                "payment_reference": doc.name
            }, fields=["name"])
            for repayment_schedule in repayment_schedules:
                repayment_schedule_doc = frappe.get_doc("Staff Loan Repayment Schedule", repayment_schedule.name)
                repayment_schedule_doc.payment_reference = ""
                repayment_schedule_doc.is_paid = 0
                repayment_schedule_doc.save()

@frappe.whitelist()
def update_additional_salary(amount,loan,payment_date,loan_amount,input_amount,input_date,type,source):
    staff_loan = frappe.get_doc("Staff Loan", loan)
    ref_name = ""

    if type == "Deduction Amount" or type == "Dont Deduct This Month" or type == "Repayment":
        for d in staff_loan.repayment_schedule:
            if d.payment_date == datetime.strptime(input_date, "%Y-%m-%d").date():
                ref_name = d.payment_reference
        
    tot = 0

    if type == "Deduction Amount":
        for d in staff_loan.repayment_schedule:
            if d.payment_date < datetime.strptime(payment_date, "%Y-%m-%d").date() and d.is_paid == 0:
                tot += d.total_payment
        loan_amount = staff_loan.loan_amount - staff_loan.total_amount_paid
        monthly_repayment_amount = staff_loan.monthly_repayment_amount
        loan_amount -= flt(input_amount)
        loan_amount -= flt(tot)
        loan_amounte = staff_loan.loan_amount - staff_loan.total_amount_paid
        loan_amounte -= flt(tot)
        if loan_amounte < 0:
            frappe.throw("Amount can not be greater than "+ str(loan_amounte) + " for the chosen date")

    if type == "Repayment":
        for d in staff_loan.repayment_schedule:
            if d.payment_date < datetime.strptime(payment_date, "%Y-%m-%d").date() and d.is_paid == 0:
                tot += d.total_payment
        loan_amount = staff_loan.loan_amount - staff_loan.total_amount_paid
        monthly_repayment_amount = staff_loan.monthly_repayment_amount
        loan_amount -= flt(input_amount)
        if loan_amount < 0:
            frappe.throw("Amount can not be greater than "+ str(loan_amounte) + " for the chosen date")


    if type == "Monthly Deduction Amount":
        loan_amount = staff_loan.loan_amount - staff_loan.total_amount_paid
        monthly_repayment_amount = flt(input_amount)

    if type == "Deduction Till" or type == "Dont Deduct This Month":
        # frappe.throw("Amount can not be greater than for the chosen date")
        loan_amount = staff_loan.loan_amount - staff_loan.total_amount_paid
        monthly_repayment_amount = staff_loan.monthly_repayment_amount
            
        
        
    repayment_schedule = []
    payment_counter = 0
        
    while loan_amount > 0:
        payment = {}
        if type == "Deduction Till" or type == "Repayment":
                # payment_date_str = payment_date.strftime("%Y-%m-%d")
            payment_date = datetime.strptime(input_date, "%Y-%m-%d").date()
            payment["payment_date"] = payment_date.replace(day=1)
        else:
            payment_date_obj = datetime.strptime(payment_date, "%Y-%m-%d")
            next_month = payment_date_obj + relativedelta(months=1)
            payment["payment_date"] = next_month.replace(day=1)
        payment["payment_date"] = payment["payment_date"] + relativedelta(months=1 * payment_counter)

        payment["principal_amount"] = min(loan_amount, monthly_repayment_amount)

        payment["total_payment"] = payment["principal_amount"]
        loan_amount -= payment["principal_amount"]
        payment["balance_loan_amount"] = loan_amount
        repayment_schedule.append(payment)

        payment_counter += 1

    to_remove = []
    to_add = []
    if type == "Deduction Amount" or type == "Dont Deduct This Month":
        for d in staff_loan.repayment_schedule:
            if d.payment_date > datetime.strptime(payment_date, "%Y-%m-%d").date() and d.payment_reference:
                to_add.append(d)
            if d.payment_date >= datetime.strptime(payment_date, "%Y-%m-%d").date():
                to_remove.append(d)
    elif type == "Monthly Deduction Amount":
        for d in staff_loan.repayment_schedule:
            if  d.payment_reference and d.is_paid == 0:
                to_add.append(d)
            if d.is_paid == 0:
                to_remove.append(d)
    elif type == "Deduction Till":
        for d in staff_loan.repayment_schedule:
            if  d.payment_reference and d.is_paid == 0:
                to_add.append(d)
            if d.is_paid == 0:
                to_remove.append(d)
    elif type == "Repayment":
        for d in staff_loan.repayment_schedule:
            # frappe.throw(str(d.payment_date.strftime("%Y-%m-%d")) + str(datetime.strptime(input_date, "%Y-%m-%d").date()))
            if d.payment_date > datetime.strptime(input_date, "%Y-%m-%d").date() and d.payment_reference:
                to_add.append(d)
            if d.is_paid == 0:
                to_remove.append(d)

    for d in to_remove:
        staff_loan.remove(d)
    for i, d in enumerate(staff_loan.repayment_schedule):
        d.idx = i + 1

    if type == "Deduction Amount" or type == "Repayment":
        loan_amountt = staff_loan.loan_amount - staff_loan.total_amount_paid
        loan_amountt -= flt(input_amount)
        loan_amountt -= flt(tot)
            
            # payment_date_str = datetime.strftime(payment_date,"%Y-%m-%d")
        if type == "Repayment":
            payment_dt = datetime.strptime(input_date, "%Y-%m-%d").date()
        else:
            payment_dt = datetime.strptime(payment_date, "%Y-%m-%d")
            payment_dt = payment_dt.replace(day=1)

        if type == "Repayment":
            loan_amountt = staff_loan.loan_amount - staff_loan.total_amount_paid
            loan_amountt -= flt(input_amount)
            staff_loan.append("repayment_schedule", {
                "payment_date": payment_dt.strftime("%Y-%m-%d"),
                "principal_amount": 0,
                "total_payment": input_amount,
                "balance_loan_amount": loan_amountt,
                "is_paid": 1,
                "outsource": 1,
                "repayment_reference": source

            })
            staff_loan.total_amount_paid += flt(input_amount)
        if ref_name:
            ammendment_ref = ""
            doc = frappe.get_doc("Additional Salary", ref_name)
                # frappe.throw(str(payment_dt.strftime("%Y-%m-%d")) + " " + str(doc.payroll_date))
            if flt(amount) == doc.amount and doc.payroll_date.strftime("%Y-%m-%d") == payment_dt.strftime("%Y-%m-%d"):
                    # frappe.throw("here")
                ammendment_ref = ref_name
            else:
                doc.cancel()
                doc.reload()
                amendment = frappe.copy_doc(doc)
                amendment.docstatus = 0
                amendment.amended_from = doc.name
                amendment.amount = flt(amount) 
                amendment.payroll_date = payment_dt.strftime("%Y-%m-%d")
                amendment.save()
                amendment.submit()
                ammendment_ref = amendment.name
            if ammendment_ref:
                        # frappe.msgprint("here" + str(amendment.name))
                staff_loan.append("repayment_schedule", {
                    "payment_date": payment_dt.strftime("%Y-%m-%d"),
                    "principal_amount": 0,
                    "total_payment": input_amount,
                    "balance_loan_amount": loan_amountt,
                    "is_paid": 0,
                    "outsource": 0,
                    "payment_reference": ammendment_ref

                    })
        else:
            if type == "Deduction Amount":
                staff_loan.append("repayment_schedule", {
                    "payment_date": payment_dt.strftime("%Y-%m-%d"),
                    "principal_amount": 0,
                    "total_payment": input_amount,
                    "balance_loan_amount": loan_amountt,
                    "is_paid": 0,
                    "outsource": 0,
                    "payment_reference": ""

                    })
                
                
    if type == "Dont Deduct This Month":
        if ref_name:
            ammendment_ref = ""
            doc = frappe.get_doc("Additional Salary", ref_name)
            doc.cancel()
            doc.reload()

    for existing_d in to_add:
        is_used = False
        for d in repayment_schedule:
            if existing_d.payment_date.strftime("%Y-%m-%d") == d["payment_date"].strftime("%Y-%m-%d"):
                is_used = True
                break
        if not is_used:
            doc = frappe.get_doc("Additional Salary", existing_d.payment_reference)
            doc.cancel()

    for d in repayment_schedule:
        payment_date = d["payment_date"]
        payment_datee = payment_date.replace(day=1)
        existing_payment = None
        for existing_d in to_add:
            if existing_d.payment_date.strftime("%Y-%m-%d") == payment_date.strftime("%Y-%m-%d"):
                    # frappe.throw("here First: " + str(payment_date.strftime("%Y-%m-%d")) + " " + str(existing_d.payment_date))
                existing_payment = existing_d
                break
        if existing_payment:
            amendment_name = ""
            doc = frappe.get_doc("Additional Salary", existing_payment.payment_reference)
            if d["total_payment"] == doc.amount and doc.payroll_date.strftime("%Y-%m-%d") == payment_datee.strftime("%Y-%m-%d"):
                    # frappe.throw(str(payment_datee.strftime("%Y-%m-%d")) + " " + str(doc.payroll_date))
                amendment_name = existing_payment.payment_reference
            else:
                doc.cancel()
                doc.reload()
                amendment = frappe.copy_doc(doc)
                amendment.docstatus = 0
                amendment.amended_from = doc.name
                amendment.amount = d["total_payment"] 
                amendment.payroll_date = payment_datee.strftime("%Y-%m-%d")
                amendment.save()
                amendment.submit()
                amendment_name = amendment.name
            if amendment_name:
                    # frappe.msgprint("here: " + str(existing_payment.payment_reference))
                staff_loan.append("repayment_schedule", {
                    "payment_date": payment_datee.strftime("%Y-%m-%d"),
                    "principal_amount": 0,
                    "total_payment": d["total_payment"],
                    "payment_reference": amendment_name,
                    "balance_loan_amount": d["balance_loan_amount"],
                    "is_paid": 0
                })
            else: 
                staff_loan.append("repayment_schedule", {
                    "payment_date": payment_datee.strftime("%Y-%m-%d"),
                    "principal_amount": 0,
                    "total_payment": d["total_payment"],
                    "payment_reference": amendment_name,
                    "balance_loan_amount": d["balance_loan_amount"],
                    "is_paid": 0
                })
        else:
            staff_loan.append("repayment_schedule", {
                "payment_date": payment_datee.strftime("%Y-%m-%d"),
                "principal_amount": 0,
                "total_payment": d["total_payment"],
                "balance_loan_amount": d["balance_loan_amount"],
                "is_paid": 0
            })
		
    staff_loan.save()
    if staff_loan.save():
        frappe.msgprint("Loan Schedule Updated")
    return "pass"
    # else:
    #     for d in staff_loan.repayment_schedule:
    #         if d.payment_reference == ref_name:
    #             d.payment_reference = ""
    #             d.is_paid = 0
    #             d.save()
    #             if d.save():
    #                 additional_salary = frappe.get_doc("Additional Salary", ref_name)
    #                 additional_salary.cancel()
    #                 # additional_salary.delete()
    #     return 1