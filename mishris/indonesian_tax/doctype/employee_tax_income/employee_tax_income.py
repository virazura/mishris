# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import throw, _
from frappe.utils import flt, cint, getdate, datetime, date_diff
from frappe.model.document import Document

from six import string_types


class BracketNotFound(frappe.ValidationError): pass
class PTKPNotFound(frappe.ValidationError): pass

class EmployeeTaxIncome(Document):

    def validate(self):
        if not (len(self.get("earnings")) or len(self.get("deductions"))):
            # get details from salary structure
            self.get_emp_and_leave_details()
        else:
            self.get_leave_details(lwp = self.leave_without_pay)

    def get_emp_and_leave_details(self):
        '''First time, load all the components from salary structure'''
        if self.employee:
            self.set("earnings", [])
            self.set("deductions", [])

            # if not self.salary_slip_based_on_timesheet:
            #     self.get_date_details()
            # self.validate_dates()
            joining_date, relieving_date = frappe.db.get_value("Employee", self.employee,
                ["date_of_joining", "relieving_date"])

            # self.get_leave_details(joining_date, relieving_date)
            slip = frappe.get_doc('Salary Slip', {'employee': self.employee})
            struct = self.check_sal_struct(joining_date, relieving_date, slip)

            # if struct:
            #     self._salary_structure_doc = frappe.get_doc('Salary Structure', struct)
            #     self.salary_slip_based_on_timesheet = self._salary_structure_doc.salary_slip_based_on_timesheet or 0
            #     self.set_time_sheet()
            #     self.pull_sal_struct()

    def check_sal_struct(self, joining_date, relieving_date, salary_slip):
        cond = """and sa.employee=%(employee)s and (sa.from_date <= %(start_date)s or
                sa.from_date <= %(end_date)s or sa.from_date <= %(joining_date)s)"""
        if salary_slip.payroll_frequency:
            cond += """and ss.payroll_frequency = '%(payroll_frequency)s'""" % {"payroll_frequency": salary_slip.payroll_frequency}

        st_name = frappe.db.sql("""
            select sa.salary_structure
            from `tabSalary Structure Assignment` sa join `tabSalary Structure` ss
            where sa.salary_structure=ss.name
                and sa.docstatus = 1 and ss.docstatus = 1 and ss.is_active ='Yes' %s
            order by sa.from_date desc
            limit 1
        """ %cond, {'employee': self.employee, 'start_date': salary_slip.start_date,
            'end_date': salary_slip.end_date, 'joining_date': joining_date})

        if st_name:
            self.salary_structure = st_name[0][0]
            return self.salary_structure

        else:
            self.salary_structure = None
            frappe.msgprint(_("No active or default Salary Structure found for employee {0} for the given dates")
                .format(self.employee), title=_('Salary Structure Missing'))
    pass
@frappe.whitelist()
def calculate_tax(salary_slip):
    """
        mishris.indonesian_tax.doctype.employee_tax_income.employee_tax_income
        Calculate Income Tax based on PPH 21 
        Which Create by Financial Ministry of Indonesi

        params: Salary Slip Object
        return: Tax Object
    """

    if isinstance(salary_slip, string_types):
        salary_slip = json.loads(salary_slip)
        salary_slip = frappe._dict(salary_slip)

    # change str to datetime.date type
    salary_slip.update({
        'start_date': getdate(salary_slip.start_date),
        'end_date': getdate(salary_slip.end_date)
        })

    #check tax type for employee
    employment = check_employee_type(salary_slip)
    salary_slip.update({
        'date_of_joining':employment.date_of_joining,
        'marital_status':  employment.marital_status,
        'dependant': employment.dependant,
        'annualized': 12,
        'resignation': employment.resignation or None,
        'non_employee': employment.non_employee,
        'working_month': employment.working_month,
        'annualized': employment.annualized,
        'expatriat': employment.expatriat
        })

    if salary_slip.non_employee == 1:
        tax_amount, tax_regular, tax_iregular = calculate_tax_non_employee(salary_slip)
    else:
        tax_amount, tax_regular, tax_iregular = calculate_tax_employee(salary_slip)

    print(tax_iregular)
    if employment.npwp is None:
        tax_amount = (tax_amount * 0.2) + tax_amount
        tax_regular = (tax_regular * 0.2) + tax_regular
        tax_iregular = (tax_iregular * 0.2) + tax_iregular

    salary_slip.update({
        'tax_amount' :tax_amount,
        'tax_regular' : tax_regular or 0,
        'tax_iregular' : tax_iregular or 0
        })

    return salary_slip

def check_employee_type(salary_slip):
    employee = frappe.get_doc('Employee', {"employee": salary_slip.employee})
    employment_type = frappe.get_doc('Employment Type', {'employee_type_name': employee.employment_type})

    working_days = salary_slip.end_date - employee.date_of_joining
    working_month = salary_slip.end_date.month

    salary_slip.update({
        'date_of_joining':employee.date_of_joining,
        'marital_status':  employee.new_marital_status,
        'dependant': employee.dependant,
        'annualized': 12,
        'resignation': employee.reason_for_resignation or None,
        'non_employee': employment_type.non_employee,
        'working_month': working_month,
        'expatriat': 0,
        'npwp': employee.npwp
    })    
    fiscal_year = '%s-01-01' % salary_slip.end_date.year
    if employment_type.non_employee == 0:
        if employee.date_of_joining > getdate(fiscal_year):
            annualized = 12 - salary_slip.date_of_joining.month
            salary_slip.update({
                'annualized': annualized
                })

        if employee.nationality != 'Indonesia':
            expatriat = 1   
            salary_slip.update({
                'expatriat': expatriat
                })

    return salary_slip

def calculate_tax_employee(salary_slip):
    regular, iregular, is_iregular = annualized_salary_slip(salary_slip)
    if salary_slip.end_date.month == 12:
        salary_accumulated, tax_accumulated = tax_last_period(salary_slip)
        gross_pay, earning_iregular = recalculate_salary_slip(salary_slip)
        regular = salary_accumulated + gross_pay + earning_iregular
        iregular = regular

    marital_status = salary_slip.marital_status
    dependant = salary_slip.dependant

    # Baru dicari Pajak Terutangnya
    taxable_regular = taxable_income(regular, marital_status, dependant)
    annualized_tax_regular, bracket = get_bracket(taxable_regular)
    tax_regular = calculate_tax_paid(salary_slip, annualized_tax_regular)

    tax_iregular = 0
    tax = tax_regular

    print(is_iregular, 'iregular')
    if is_iregular == 1:
        taxable_irregular = taxable_income(iregular, marital_status, dependant)   
        annualized_tax_iregular, bracket = get_bracket(taxable_irregular)
        tax_iregular = calculate_tax_paid(salary_slip, annualized_tax_iregular)
        tax = flt(tax_regular, 3) + (flt(tax_iregular, 3) - flt(tax_regular,3))

    if salary_slip.end_date.month == 12 or salary_slip.resignation:
        tax_regular = annualized_tax_regular - tax_accumulated        
        tax = tax_regular

    return tax, tax_regular, tax_iregular

def calculate_tax_non_employee(salary_slip):
    employee = salary_slip.employee
    year = str(salary_slip.end_date).split('-')[0]
    date = salary_slip.end_date
    condition = "and end_date < '%s'" % date
    salaries = []

    salaries = employee_salaries(employee, year, date, condition)
    salary_accumulation = sum([nt.net_pay for nt in salaries])

    condition = 'limit 1'
    last_slip = employee_salaries(employee, year, date, condition)

    paid_tax = 0
    if len(last_slip) < 0:
        paid_tax = last_slip[0].tax_amount

    tax_regular = 0
    tax_iregular = 0

    income_accumulation = salary_slip.net_pay + salary_accumulation
    tax_month, bracket = get_bracket(income_accumulation)
    tax_must_paid = tax_month - paid_tax

    return tax_must_paid, tax_regular, tax_iregular

def calculate_tax_paid(salary_slip, annualized_tax, tax_paid=None):
    fiscal_year = '%s-01-01' % salary_slip.end_date.year

    if salary_slip.annualized != 12:
        salary_slip.working_month = salary_slip.working_month or salary_slip.end_date.month

    tax_amount = annualized_tax / salary_slip.annualized
    print(salary_slip.annualized)
    if salary_slip.expatriat == 1 or salary_slip.resignation is 'Passed Away':
        if salary_slip.date_of_joining > getdate(fiscal_year):
            salary_slip.working_month = (salary_slip.end_date.month - salary_slip.date_of_joining.month) or 1

        annualized_tax = annualized_tax * salary_slip.working_month / 12
        tax_amount = 1 / salary_slip.working_month * annualized_tax

    if tax_paid != None:
        tax_amount = tax_amount - tax_paid

    return tax_amount

def annualized_salary_slip(salary_slip, v='two'):
    is_iregular = 0
    fiscal_year = '%s-01-01' % salary_slip.end_date.year

    gross_pay, earning_iregular = recalculate_salary_slip(salary_slip)

    print(earning_iregular, 'earning_iregular')    
    if earning_iregular:
        is_iregular = 1

    if v =='one':
        annualized_salary_regular = gross_pay * salary_slip.annualized
        annualized_salary_iregular = annualized_salary_regular + earning_iregular
    elif v =='two':
        salary = flt(gross_pay) + flt(earning_iregular)
        annualized_salary_regular = flt(gross_pay) * salary_slip.annualized
        annualized_salary_iregular = flt(salary) * salary_slip.annualized

    if salary_slip.expatriat == 1 or salary_slip.resignation is 'Passed Away':
        if salary_slip.date_of_joining > getdate(fiscal_year):
            salary_slip.working_month = (salary_slip.end_date.month - salary_slip.date_of_joining.month) or 1

        # Pengali sesuai dengan jumlah bulan dia bekerja dibagi 12.
        annualized_salary_regular = (gross_pay * salary_slip.working_month) * 12 / salary_slip.working_month
        annualized_salary_iregular = (salary * salary_slip.working_month) * 12 / salary_slip.working_month + earning_iregular
    return annualized_salary_regular, annualized_salary_iregular, is_iregular

def recalculate_salary_slip(salary_slip):
    def sum_components(components):
        iregular = 0
        regular = 0
        for component in components:
            salary_component  = frappe.get_doc('Salary Component', {'salary_component': component.salary_component})
            if salary_component.name == component.salary_component:
                if salary_component.is_iregular:
                    iregular += flt(component.amount)
                else:
                    regular += flt(component.amount)

        return regular, iregular
    earning, earning_iregular = sum_components(salary_slip.earnings)
    total_deduction  = sum_components(salary_slip.deductions)

    salary = flt(earning) - flt(total_deduction[0])
    print(earning_iregular, 'recalculate_salary_slip')
    return salary, earning_iregular

def employee_salaries(employee, fiscal_year, date, conditions=None):
    condition = 'order by end_date desc'
    if conditions is not None:
        condition += conditions
    
    salary_slips = frappe.db.sql("""select * 
        from `tabSalary Slip`
        where employee='{employee}'
        and status='Submitted'
        and year(end_date)='{fiscal_year}'
        {conditions}""".format(employee = employee
            , fiscal_year = fiscal_year
            , conditions = conditions)
        , as_dict=1)

    return salary_slips

def tax_last_period(salary_slip):
    employee = salary_slip.employee
    fiscal_year = salary_slip.end_date.year
    date = salary_slip.end_date
    condition = "and end_date < '%s'" % date
    net_salary = employee_salaries(employee, fiscal_year, date, conditions=condition)
    salary_accumulated = sum([nt.net_pay for nt in net_salary])
    tax_accumulated = sum([nt.tax_amount for nt in net_salary])
    return salary_accumulated, tax_accumulated

def taxable_income(income, marital_status, employee_dependant):
    # Find Dependant and Marital Status
    dependant = frappe.get_doc("Dependant", {"name": employee_dependant, "marital_status": marital_status})
    non_taxable = frappe.get_doc('Non Taxable Income', {'dependant':dependant.name})

    if not non_taxable:
        throw(_('PTPK not found. Please setting up in HR Addon'), PTKPNotFound)

    taxable = income - flt(non_taxable.nominal_non_tax) - flt(non_taxable.variable)
    return taxable

def get_bracket(annualized_tax):
    from operator import itemgetter
    brackets = frappe.db.sql("""Select * from `tabTax Bracket`""", as_dict=1)
    if len(brackets) <= 0:
        frappe.throw(_('Tarif Pajak {0} ditemukan. Silahkan isi di Tax Bracket'.format(len(brackets))), BracketNotFound)
    
    brackets = sorted(brackets, key=itemgetter('priority')) 
    taxs = []
    allowed_tax = annualized_tax
    for bracket in brackets:
        if allowed_tax > 0 and allowed_tax >= flt(bracket.max_income) and flt(bracket.max_income) != 0:
            tax = flt(bracket.max_income) * flt(bracket.precentage) / 100
            taxs.append(tax)
        else:
            tax = flt(allowed_tax) * flt(bracket.precentage) / 100
            taxs.append(tax)

        allowed_tax = allowed_tax - flt(bracket.max_income)
    taxs = [s for s in taxs if s > 0]
    tax = sum(taxs)
    return tax, len(taxs)
