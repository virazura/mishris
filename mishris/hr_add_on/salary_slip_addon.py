from __future__ import unicode_literals
import frappe
from datetime import datetime
from mishris.hr_add_on.doctype.overtime_record.overtime_record import get_total_amount
from mishris.indonesian_tax.doctype.employee_tax_income.employee_tax_income import calculate_tax
from erpnext.hr.doctype.salary_slip.salary_slip import SalarySlip

def salary_slip_detail(doc, event):
    overtime_amount = get_total_amount(doc.employee, doc.start_date, doc.end_date)
    tax_income = calculate_tax(doc)

    doc.overtime_amount = overtime_amount
    doc.tax_amount = tax_income.tax_amount
    doc.tax_regular = tax_income.tax_regular
    doc.tax_iregular = tax_income.tax_iregular
    doc.bracket = tax_income.bracket

    for component in doc.earnings:
        component.is_iregular = get_salary_slip_row(component.salary_component)['is_iregular']

    for component in doc.deductions:
        component.is_iregular = get_salary_slip_row(component.salary_component)['is_iregular']

def get_salary_slip_row(salary_component):
    component = frappe.get_doc("Salary Component", {'salary_component':salary_component})
    # Data for update_component_row
    struct_row = {}
    struct_row['is_iregular'] = component.is_iregular
    return struct_row
