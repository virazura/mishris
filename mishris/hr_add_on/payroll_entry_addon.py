
from __future__ import unicode_literals
import frappe
import pandas as pd
import re, csv, os, sys
from frappe.utils.csvutils import UnicodeWriter
from frappe.utils import cstr, formatdate, format_datetime
from frappe.core.doctype.data_import.importer import get_data_keys
from six import string_types
from frappe.utils import flt, cint, getdate, datetime, date_diff


@frappe.whitelist()
def export_bank_entry():
    args = frappe.local.form_dict
    payroll_entry = frappe.get_doc('Payroll Entry', {'name': args['payroll_entry']})
    bca = [
        [
        "Acc. No.","Trans. Amount","emp.Name"
        ]
    ]
    non_bca =[
        ["Acc. No. To",
            "Trans. Amount",
            "BI Code",
            "Bank Name",
            "Bank Branch Name",
            "Receiver Name",
            "Jenis",
            "Customer Type",
            "Customer Residence"
        ]
    ]
    xslx_data = []
    header = bca
    bank = 'BCA'
    if args['bank_name'] == 'Other':    
        header = non_bca
        bank = 'Non BCA'

    xslx_data = add_header(xslx_data, header)
    xslx_data = add_data(xslx_data, args, bank)

    from frappe.utils.xlsxutils import make_xlsx
    xlsx_file = make_xlsx(xslx_data,
            "Payroll {} {} {} - {}.xlsx".format(
            payroll_entry.company, bank, payroll_entry.start_date, payroll_entry.end_date
            )
        )
    
    frappe.response["filename"] = "Payroll {} {} {} - {}.xlsx".format(
        payroll_entry.company, bank, payroll_entry.start_date, payroll_entry.end_date
    )
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'

def add_header(w, header):
    for r in header:
        w.append(r)
    return w

def add_data(w, args, bank):
    if bank == 'Non BCA':
        data = get_data_other_bank(args)
    else:
        data = get_data(args)

    for r in data:
        w.append(r)
    return w

def get_data(args):
    payroll_entry = args['payroll_entry']
    bank = frappe.get_doc('Bank', {'bank_code': '0140012'})

    condition = "and bank_name = '{0}'".format(bank.bank_name)
    if args['bank_name'] != 'BCA':
        condition = "and NOT bank_name = '{0}'".format(bank.bank_name)

    slips = frappe.db.sql("""SELECT bank_name, bank_account_no, 
            employee_name, net_pay FROM `tabSalary Slip` 
            where `payroll_entry` = '{payroll_entry}' {condition}"""
            .format(payroll_entry=payroll_entry,
                condition = condition), as_dict=True)
    data = []

    for slip in slips:
        row = []
        row.append(slip.bank_account_no)
        row.append(flt(slip.net_pay))
        row.append(slip.employee_name)
        data.append(row)
    return data

def get_data_other_bank(args):
    payroll_entry = args['payroll_entry']
    condition = "and bank_name = 'Bank Central Asia'"
    bank = frappe.get_doc('Bank', {'bank_code': '0140012'})

    if args['bank_name'] != 'BCA':
        condition = "and NOT bank_name = '{0}'".format(bank.bank_name)

    slips = frappe.db.sql("""SELECT bank_name, bank_account_no, 
            employee_name, net_pay FROM `tabSalary Slip` 
            where `payroll_entry` = '{payroll_entry}' {condition}"""
            .format(payroll_entry=payroll_entry,
                condition = condition), as_dict=1)
    data = []
    for slip in slips:
        row = []
        row.append(slip.bank_account_no)
        row.append(flt(slip.net_pay))
        bank = frappe.get_doc('Bank', {'bank_name': slip.bank_name})
        row.append(bank.bank_code)
        row.append(slip.bank_name)
        row.append('Jakarta')
        row.append(slip.employee_name)
        row.append('LLG')
        row.append('R')
        row.append('1')
        data.append(row)

    return data
