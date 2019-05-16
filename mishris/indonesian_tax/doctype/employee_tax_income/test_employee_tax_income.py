#-*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
import os
import json
import calendar
import erpnext
from frappe.utils.make_random import get_random
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import nowdate, add_days, add_years, getdate, add_months
from erpnext.hr.doctype.salary_structure.salary_structure import make_salary_slip
from erpnext.hr.doctype.employee.test_employee import make_employee


class TestEmployeeTaxIncome(unittest.TestCase):
    def setUp(self):
        frappe.db.set_value("HR Settings", None, "email_salary_slip_to_employee", 0)
    
    def tearDown(self):
        frappe.set_user("Administrator")

    def test_calculate_tax(self):
        from mishris.indonesian_tax.tax_calculator  import _calculate_tax
        ss = make_salary_slip()
        
        tax = _calculate_tax(ss)
        self.assertEqual(tax.payroll_date, '31-01-2019')
        self.assertEqual(tax.net_pay, 1000000000)
        self.assertEqual(tax.taxable_income, 11946000000.0)
        self.assertEqual(tax.bracket, 4)
        self.assertEqual(tax.progressif_amount, 3508800000)
        self.assertEqual(tax.tax_amount, 292400000)

    def test_iregular_tax(self):
        from mishris.indonesian_tax.tax_calculator  import _calculate_tax
        ss = make_salary_slip()
        ss.update({
            'iregular': 1,
            'iregular_amount': 10000000
            })
        tax = _calculate_tax(ss)
        self.assertEqual(tax.payroll_date, '31-01-2019')
        self.assertEqual(tax.net_pay, 1000000000)
        self.assertEqual(tax.taxable_income, 11946000000.0)
        self.assertEqual(tax.bracket, 4)
        self.assertEqual(tax.progressif_amount, 3508800000)
        self.assertEqual(tax.tax_amount, 292650000.0)
        self.assertEqual(tax.tax_regular, 292400000.0)
        self.assertEqual(tax.tax_iregular, 292650000.0)

    def test_expatriat_tax(self):
        from mishris.indonesian_tax.tax_calculator  import _calculate_tax
        ss = make_salary_slip()
        ss.update({
            'payroll_date'   : '30-12-2019',
            'expatriat'      : 1,
            'date_of_joining'   : '20-03-2019',
            })
        tax = _calculate_tax(ss)
        self.assertEqual(tax.payroll_date, '30-12-2019')
        self.assertEqual(tax.net_pay, 1000000000)
        self.assertEqual(tax.taxable_income, 11946000000.0)
        self.assertEqual(tax.bracket, 4)
        self.assertEqual(tax.progressif_amount, 3508800000)
        self.assertEqual(tax.tax_amount, 292400000.0)
        self.assertEqual(tax.tax_regular, 292400000.0)

    def test_non_employee_tax(self):
        from mishris.indonesian_tax.tax_calculator  import  calculate_tax_non_employee
        ss = make_salary_slip()
        ss.update({
            'net_pay' : 10000000,
            'payroll_date'   : '30-03-2019'
            })
        last_paid_tax = 0
        salary_accumulation = 0
        tax = calculate_tax_non_employee(ss, salary_accumulation, last_paid_tax)
        self.assertEqual(tax.bracket, 1)
        self.assertEqual(tax.progressif_amount, 500000.0)
        self.assertEqual(tax.tax_amount, 500000.0)

def make_salary_slip():
    salary_slip = frappe._dict()
    salary_slip.update({
        'date_of_joining': '06-06-2016',
        'payroll_date'   : '31-01-2019',
        'gross_pay'      : 2000000000,
        'iregular'       : 0,
        'is_annualized'  : 0,
        'ireguler_amount': 0,
        'is_net'         : 1,
        'salary'         : 0,
        'net_pay'        : 1000000000,
        'slip_taxed'     : 0,
        'marital_status' : 'Single',
        'dependant'      : 'Tanpa Tanggungan',
        'annualized'     : 12,
        'resignation'    : None,
        'non_employee'   : 0,
        'working_month'  : 1,
        'expatriat'      : 0,
        'npwp'           : 123123123123
    })
    return salary_slip

def create_account(company):# {{{
    """
        Must search how to set default account have number
        Because ERPNext not include number in Account
    """
    salary_account = frappe.db.get_value("Account", "Salary - " + frappe.get_cached_value('Company',  company,  'abbr'))
    if not salary_account:
        frappe.get_doc({
        "doctype": "Account",
        "account_name": "Salary",
        "parent_account": "Indirect Expenses - " + frappe.get_cached_value('Company',  company,  'abbr'),
        "company": company
        }).insert()
    return salary_account
# }}}
def get_salary_component_account(sal_comp):# {{{
    company = erpnext.get_default_company()
    sal_comp = frappe.get_doc("Salary Component", sal_comp)
    if not sal_comp.get("accounts"):
        sal_comp.append("accounts", {
            "company": company,
            "default_account": create_account(company)
        })
        sal_comp.save()
# }}}
def make_salary_component(salary_components, test_tax):# {{{
    for salary_component in salary_components:
        if not frappe.db.exists('Salary Component', salary_component["salary_component"]):
            if test_tax:
                if salary_component["type"] == "Earning":
                    salary_component["is_tax_applicable"] = 1
                elif salary_component["salary_component"] == "TDS":
                    salary_component["variable_based_on_taxable_salary"] = 1
                    salary_component["amount_based_on_formula"] = 0
                    salary_component["amount"] = 0
                    salary_component["formula"] = ""
                    salary_component["condition"] = ""
            salary_component["doctype"] = "Salary Component"
            salary_component["salary_component_abbr"] = salary_component["abbr"]
            frappe.get_doc(salary_component).insert()
        get_salary_component_account(salary_component["salary_component"])
# }}}
def make_earning_salary_component(setup=False, test_tax=False):# {{{
    data = [
            {
                "salary_component": 'Basic Salary',
                "abbr":'BS',
                "condition": 'base',
                "formula": 'base',
                "type": "Earning",
                "amount_based_on_formula": 1
            }
            # {
            #     "salary_component": 'BPJS',
            #     "abbr":'BP',
            #     "condition": 'base > 8000000',
            #     "formula": '320000',
            #     "amount_based_on_formula": 1,
            #     "type": "Earning"
            # },e
            # {
            #     "salary_component": 'JKK dan JKM',
            #     "abbr":'JK',
            #     "condition": '',
            #     "formula": 'BS * 0.54/100',
            #     "amount_based_on_formula": 1,
            #     "type": "Earning",
            # },
            # {
            #     "salary_component": "Lembur dan Tunjangan Lain",
            #     "abbr": 'LT',
            #     "condition": 'end_date == "2019-03-30"',
            #     "amount": '5000000',
            #     "is_additional_component": 1,
            #     "type": "Earning",
            #     "is_iregular": 1
            # }
        ]
    setup=False
    if setup:
        data = [
            {
                "salary_component": "Commission",
                "abbr": 'Commission',
                "formula": 'base',
                "type": "Earning"
            }
        ]
    make_salary_component(data, test_tax)
    return data
# }}}
def make_deduction_salary_component(setup=True, test_tax=False, component=None):# {{{
    data =  [
                {
                    "salary_component": 'Professional Tax',
                    "abbr":'PT',
                    "condition": '(gross_pay*5/100)>=500000',
                    "amount": '500000',
                    "type": "Deduction",
                }
                # {
                #     "salary_component": 'JHT',
                #     "abbr":'JP',
                #     "formula": 'BS*2/100',
                #     "type": "Deduction",
                #     "amount_based_on_formula": 1
                # },
                # {
                #     "salary_component": 'JP',
                #     "abbr":'JP',
                #     "amount": '80940',
                #     "type": "Deduction",
                #     "amount_based_on_formula": 1
                # },
                # {
                #     "salary_component": 'Tanggungan BPJS',
                #     "abbr":'TBPJS',
                #     "condition": 'base > 8000000',
                #     "formula": '320000',
                #     "type": "Deduction",
                #     "amount_based_on_formula": 1
                # }
            ]
    make_salary_component(data, test_tax)
    return data
# }}}
def make_salary_structure(salary_structure, payroll_frequency, employee=None, custom=False, dont_submit=False\
    , other_details=None, test_tax=False, from_date=None):# {{{
    if test_tax:
        frappe.db.sql("""delete from `tabSalary Structure` where name=%s""",(salary_structure))
    if not frappe.db.exists('Salary Structure', salary_structure):
        details = {
            "doctype": "Salary Structure",
            "name": salary_structure,
            "company": erpnext.get_default_company(),
            "earnings": make_earning_salary_component(setup=custom, test_tax=test_tax),
            "deductions": make_deduction_salary_component(setup=custom, test_tax=test_tax),
            "payroll_frequency": payroll_frequency,
            "payment_account": get_random("Account")
        }
        if other_details and isinstance(other_details, dict):
            details.update(other_details)
        salary_structure_doc = frappe.get_doc(details).insert()
        if not dont_submit:
            salary_structure_doc.submit()
    else:
        salary_structure_doc = frappe.get_doc("Salary Structure", salary_structure)


    if employee and not frappe.db.get_value("Salary Structure Assignment",
        {'employee':employee, 'docstatus': 1}) and salary_structure_doc.docstatus==1:
            create_salary_structure_assignment(employee, salary_structure, from_date=from_date)

    return salary_structure_doc
# }}}
def make_employee_salary_slip(user, payroll_frequency, salary_structure=None, name_structure=None, from_date=None):# {{{

    employee = frappe.db.get_value("Employee", {"user_id": user})
    salary_structure_doc = salary_structure
    if not name_structure:
        name_structure = payroll_frequency + " Salary Structure Test for Salary Slip"    
    if not salary_structure:
        salary_structure_doc = make_salary_structure(name_structure, payroll_frequency, employee, from_date=from_date)

    salary_slip = frappe.db.get_value("Salary Slip", {"employee": frappe.db.get_value("Employee", {"user_id": user})})
    if not salary_slip:
        salary_slip = make_salary_slip(salary_structure_doc.name, employee = employee)
        salary_slip.employee_name = frappe.get_value("Employee", {"name":frappe.db.get_value("Employee", {"user_id": user})}, "employee_name")
        salary_slip.payroll_frequency = payroll_frequency
        salary_slip.posting_date = nowdate()
        salary_slip.insert()
        # salary_slip.submit()
        # salary_slip = salary_slip.name
    return salary_slip# }}}

def create_salary_structure_assignment(employee, salary_structure, from_date=None):# {{{
    if frappe.db.exists("Salary Structure Assignment", {"employee": employee}):
        frappe.db.sql("""delete from `tabSalary Structure Assignment` where employee=%s""",(employee))
    salary_structure_assignment = frappe.new_doc("Salary Structure Assignment")
    salary_structure_assignment.employee = employee
    salary_structure_assignment.base = 20000000
    salary_structure_assignment.variable = 0
    salary_structure_assignment.from_date = from_date or add_months(nowdate(), -1)
    salary_structure_assignment.salary_structure = salary_structure
    salary_structure_assignment.company = erpnext.get_default_company()
    salary_structure_assignment.save(ignore_permissions=True)
    salary_structure_assignment.submit()
    return salary_structure_assignment# }}}
def get_tax_paid_in_period(employee):# {{{
    tax_paid_amount = frappe.db.sql("""select sum(sd.amount) from `tabSalary Detail`
        sd join `tabSalary Slip` ss where ss.name=sd.parent and ss.employee=%s
        and ss.docstatus=1 and sd.salary_component='TDS'""", (employee))
    return tax_paid_amount[0][0]
# }}}
def create_exemption_declaration(employee, payroll_period):# {{{
    create_exemption_category()
    declaration = frappe.get_doc({"doctype": "Employee Tax Exemption Declaration",
                                    "employee": employee,
                                    "payroll_period": payroll_period,
                                    "company": erpnext.get_default_company()})
    declaration.append("declarations", {"exemption_sub_category": "_Test Sub Category",
                            "exemption_category": "_Test Category",
                            "amount": 100000})
    declaration.submit()
# }}}
def create_proof_submission(employee, payroll_period, amount):# {{{
    submission_date = add_months(payroll_period.start_date, random.randint(0, 11))
    proof_submission = frappe.get_doc({"doctype": "Employee Tax Exemption Proof Submission",
                                    "employee": employee,
                                    "payroll_period": payroll_period.name,
                                    "submission_date": submission_date})
    proof_submission.append("tax_exemption_proofs", {"exemption_sub_category": "_Test Sub Category",
                "exemption_category": "_Test Category", "type_of_proof": "Test", "amount": amount})
    proof_submission.submit()
    return submission_date
# }}}
def create_benefit_claim(employee, payroll_period, amount, component):# {{{
    claim_date = add_months(payroll_period.start_date, random.randint(0, 11))
    frappe.get_doc({"doctype": "Employee Benefit Claim", "employee": employee,
        "claimed_amount": amount, "claim_date": claim_date, "earning_component":
        component}).submit()
    return claim_date
# }}}
def create_tax_slab(payroll_period):# {{{
    data = [{
                "from_amount": 250000,
                "to_amount": 500000,
                "percent_deduction": 5
            },
            {
                "from_amount": 500000,
                "to_amount": 1000000,
                "percent_deduction": 20
            },
            {
                "from_amount": 1000000,
                "percent_deduction": 30
            }]
    payroll_period.taxable_salary_slabs = []
    for item in data:
        payroll_period.append("taxable_salary_slabs", item)
    payroll_period.save()
# }}}
def create_salary_slips_for_payroll_period(employee, salary_structure, payroll_period, deduct_random=True):# {{{
    deducted_dates = []
    i = 0
    while i < 12:
        slip = frappe.get_doc({"doctype": "Salary Slip", "employee": employee,
                "salary_structure": salary_structure, "frequency": "Monthly"})
        if i == 0:
            posting_date = add_days(payroll_period.start_date, 25)
        else:
            posting_date = add_months(posting_date, 1)
        if i == 11:
            slip.deduct_tax_for_unsubmitted_tax_exemption_proof = 1
            slip.deduct_tax_for_unclaimed_employee_benefits = 1
        if deduct_random and not random.randint(0, 2):
            slip.deduct_tax_for_unsubmitted_tax_exemption_proof = 1
            deducted_dates.append(posting_date)
        slip.posting_date = posting_date
        slip.start_date = get_first_day(posting_date)
        slip.end_date = get_last_day(posting_date)
        doc = make_salary_slip(salary_structure, slip, employee)
        doc.submit()
        i += 1
    return deducted_dates
# }}}
def create_additional_salary(employee, payroll_period, amount):# {{{
    salary_date = add_months(payroll_period.start_date, random.randint(0, 11))
    frappe.get_doc({"doctype": "Additional Salary", "employee": employee,
                    "company": erpnext.get_default_company(),
                    "salary_component": "Perfomance Bonus",
                    "payroll_date": salary_date,
                    "amount": amount, "type": "Earning"}).submit()
    return salary_date
# }}}

def run_tests():
    test = TestEmployeeTaxIncome()
    test.test_calculate_tax()
    test.test_iregular_tax()
    test.test_expatriat_tax()
    test.test_non_employee_tax()
