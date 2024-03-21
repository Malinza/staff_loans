
__version__ = '15.0.6'

from hrms.payroll.doctype.salary_slip import salary_slip_loan_utils
from staff_loans.Custom.button_method import custom_set_loan_repayment

salary_slip_loan_utils.set_loan_repayment = custom_set_loan_repayment