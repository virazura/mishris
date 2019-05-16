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

@frappe.whitelist()
def calculate_tax(salary_slip):
    """
        mishris.indonesian_tax.doctype.employee_tax_income.employee_tax_income
        Calculate Income Tax based on PPH 21 
        Which Create by Financial Ministry of Indonesi

        params: Salary Slip Object
        return: Tax Object
    """

def calculate_tax_employee(salary_slip, employee):
    # 1 annualized salary
    salary = annualized_salary(salary_slip)

    # find tax annualized
    non_taxable = non_taxable_income(salary, employee.marital_status, employee.dependant)

    salary_slip.progressif_tax_iregular, bracket = get_brackets(non_taxable) 
    
    if salary_slip.iregular == 1:
        salary = salary + salary_slip.iregular_amount
        non_taxable = non_taxable_income(salary, employee.marital_status, employee.dependant)
        salary_slip.progressif_tax_iregular, bracket = get_brackets(non_taxable) 
        
    tax = tax_must_paid(salary_slip)

    tax.update({
        'tax_amount': tax.tax_amount,
        'tax_reguler': tax_regular,
        'tax_iregular': tax_iregular or 0
    })
    
    return tax

def annualized_salary(salary_slip):
    
    annualized_salary = salary_slip.slip_taxed * salary_slip.annualized
   
    if salary_slip.end_date.month == 12:
        annualized_salary, tax_accumulation = last_tax_period(
                salary_slip.employee,salary_slip.end_date)
        salary_slip.tax_accumulation = tax_accumulation
        salary_slip.last_period = 1
 
    salary_slip.update({
        'annualized_salary': annualized_salary,
       })

    return salary_slip

def tax_must_paid(salary_slip):

    salary_slip.tax_amount = salary_slip.progressif_tax / salary_slip.annualized
    salary_slip.tax_regular = salary_slip.tax_amount

    if salary_slip.iregular:
        salary_slip.tax_iregular = salary_slip.progressif_tax_iregular / salary_slip.annualized
        salary_slip.tax_amount  = salary_slip.tax_regular + (salary_slip.tax_iregular - salary_slip.tax_regular)

    return salary_slip
    
def tax_last_period(employee, end_date):

    condition = "and end_date < '%s'" % date
    net_salary = employee_salaries(employee, date, conditions=condition)
    salary_accumulated = sum([nt.net_pay for nt in net_salary])
    tax_accumulated = sum([nt.tax_income for nt in net_salary])

    return salary_accumulated, tax_accumulated

def employee_salaries(employee, end_date, conditions=None):
    condition = 'order by end_date desc'
    if conditions is not None:
        condition += conditions
    
    salary_slips = frappe.db.sql("""select * 
        from `tabSalary Slip`
        where employee='{employee}' 
        and year(end_date)='{end_date}'
        {conditions}""".format(employee = employee
            , end_date = end_date
            , conditions = conditions)
        , as_dict=1)

    return salary_slips


def non_taxable_income(income, marital_status, dependant):
    # Find Dependant and Marital Status
    dependant = frappe.get_doc("Dependant", {"name": dependant, "marital_status": marital_status})
    non_taxable = frappe.get_doc('Non Taxable Income', {'dependant':dependant.name})
    total_dependant = dependant.total_dependant

    if dependant.marital_status != 'Single':
        total_dependant = dependant.total_dependant + 1
    else:
        total_dependant = dependant.total_dependant

    if not non_taxable:
        throw(_('PTPK not found. Please setting up in HR Addon'), PTKPNotFound)

    variable = flt(non_taxable.variable) * total_dependant
    taxable = income - flt(non_taxable.nominal_non_tax) - variable

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

