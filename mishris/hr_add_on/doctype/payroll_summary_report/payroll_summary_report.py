# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cstr, getdate
from frappe.utils.csvutils import UnicodeWriter


class PayrollEntryNotFoundError(frappe.ValidationError):
    pass


class PayrollSummaryReport(Document):
    pass


# @frappe.whitelist()
# def download_report():
#     _validate_permission()

#     args = frappe.local.form_dict
#     start_date = args["start_date"]
#     end_date = args["end_date"]

#     data = _prepare_data(start_date, end_date)

#     as_xlsx(data, start_date, end_date)


# def as_csv(data, start_date, end_date):

#     writer = _prepare_doc(data)
#     frappe.response["result"] = cstr(writer.getvalue())
#     frappe.response["type"] = "csv"
#     frappe.response["doctype"] = "Payroll Summary Report {} - {}".format(
#         start_date, end_date
#     )


# def as_xlsx(data, start_date, end_date):
#     from frappe.utils.xlsxutils import make_xlsx

#     earning_header = _get_salary_component(earning=True)
#     deduction_header = _get_salary_component(earning=False)

#     xlsx_data = (
#         *_get_header_list(earning_header, deduction_header),
#         *_get_data_list(earning_header, deduction_header, data),
#     )

#     xlsx_file = make_xlsx(
#         xlsx_data, "Payroll Summary Report {} - {}".format(start_date, end_date)
#     )

#     # write out response as a xlsx type
#     frappe.response["filename"] = "Payroll Summary Report {} - {}.xlsx".format(
#         start_date, end_date
#     )
#     frappe.response["filecontent"] = xlsx_file.getvalue()
#     frappe.response["type"] = "binary"


# def _validate_permission():
#     if not frappe.has_permission("Payroll Entry", "read"):
#         raise frappe.PermissionError
#     if not frappe.has_permission("Salary Slip", "read"):
#         raise frappe.PermissionError
#     if not frappe.has_permission("Company", "read"):
#         raise frappe.PermissionError


# def _prepare_data(start_date, end_date):
#     """Prepare data for report
#     summary of salary slip data between start_date and end_date

#     :param start_date: date, in str (with format 'yyyy-mm-dd') or datetime.date
#     :param end_date: date, in str (with format 'yyyy-mm-dd') or datetime.date

#     :returns: dict of the data
#     """
#     data = {}
#     start_date = getdate(start_date)
#     end_date = getdate(end_date)

#     for i in _get_all_company():
#         data[i.name] = {"company": i.name}

#     for i in data:
#         data[i]["payroll_entries"] = _get_payroll_entries(start_date, end_date, i)
#         data[i]["earnings"] = {}
#         data[i]["deductions"] = {}
#         data[i]["loan"] = 0
#         data[i]["gross_salary"] = 0
#         data[i]["net_salary"] = 0
#         data[i]["employee_now"] = 0
#         data[i]["tax"] = {}
#         for pe in data[i]["payroll_entries"]:
#             data[i]["earnings"] = _sum_dict_component(
#                 data[i]["earnings"], _get_components(pe, earnings=True)
#             )
#             data[i]["deductions"] = _sum_dict_component(
#                 data[i]["deductions"], _get_components(pe, earnings=False)
#             )
#             sum_salary = _get_sum_salary(pe)
#             data[i]["loan"] = data[i]["loan"] + sum_salary["loan"]
#             data[i]["gross_salary"] = data[i]["gross_salary"] + sum_salary["gross_pay"]
#             data[i]["net_salary"] = data[i]["net_salary"] + sum_salary["net_pay"]
#             data[i]["employee_now"] = data[i]["employee_now"] + sum_salary["count_employee"]
#             tax = {
#                 "Tax Amount": sum_salary["tax_amount"],
#                 "Tax Regular": sum_salary["tax_regular"],
#                 "Tax Iregular": sum_salary["tax_iregular"],
#             }
#             data[i]["tax"] = _sum_dict_component(
#                 data[i]["tax"], tax
#             )

#         last_payroll_entries = _get_payroll_entries(
#             add_months(start_date, -1), add_months(end_date, -1), i
#         )
#         data[i]["employee_last_month"] = 0
#         for lpe in last_payroll_entries:
#             data[i]["employee_last_month"] = data[i]["employee_last_month"] + _get_count_employee(lpe)

#         data[i]["employee_difference"] = (
#             data[i]["employee_now"] - data[i]["employee_last_month"]
#         )
#     return data


# def _sum_dict_component(first_dict, second_dict):
#     result_dict = {}
#     for key, val in first_dict.items():
#         result_dict[key] = result_dict.get(key, 0) + val
#     for key, val in second_dict.items():
#         result_dict[key] = result_dict.get(key, 0) + val
#     return result_dict


# def _get_all_company():
#     return frappe.get_list("Company")


# def _get_payroll_entry(start_date, end_date, company, filters=None):
#     filters = filters or {}
#     return frappe.get_value(
#         "Payroll Entry",
#         filters={
#             "company": company,
#             "docstatus": 1,
#             "start_date": [">=", start_date],
#             "end_date": ["<=", end_date],
#             "payroll_frequency": "Monthly",
#             **filters,
#         },
#         fieldname="name",
#     )


# def _get_payroll_entries(start_date, end_date, company, filters=None):
#     filters = filters or {}
#     payroll_entries = frappe.get_all(
#         "Payroll Entry",
#         filters={
#             "company": company,
#             "docstatus": 1,
#             "start_date": [">=", start_date],
#             "end_date": ["<=", end_date],
#             "payroll_frequency": "Monthly",
#             **filters,
#         },
#     )
#     return [i["name"] for i in payroll_entries]


# def _get_components(payroll_entry, earnings=True):
#     """Get total earnings based on payroll entry and the salary components

#     :param payroll_entry: name of payroll entry
#     :param earnings: True to get earnings component, False to get deductions component

#     :return : dict {"salary_component_name": amount}
#     """
#     earnings = frappe.db.sql(
#         """
#         SELECT
#             sde.salary_component as salary_component,
#             SUM(sde.amount) AS amount
#         FROM
#             `tabSalary Slip` ss
#                 JOIN
#             `tabSalary Detail` sde ON (sde.parent = ss.name
#                 AND sde.parenttype = 'Salary Slip'
#                 AND sde.parentfield = '{}')
#         WHERE
#             ss.payroll_entry = %s
#                 AND ss.docstatus = 1
#         GROUP BY sde.salary_component
#         ORDER BY sde.salary_component""".format(
#             "earnings" if earnings else "deductions"
#         ),
#         (payroll_entry,),
#         as_dict=True,
#     )
#     result = {i["salary_component"]: i["amount"] for i in earnings}
#     return result


# def _get_sum_salary(payroll_entry):
#     salary = frappe.db.sql(
#         """
#         SELECT
#             SUM(total_loan_repayment) AS loan,
#             SUM(gross_pay) AS gross_pay,
#             SUM(net_pay) AS net_pay,
#             SUM(tax_amount) AS tax_amount,
#             SUM(tax_regular) AS tax_regular,
#             SUM(tax_iregular) AS tax_iregular,
#             COUNT(employee) AS count_employee
#         FROM
#             `tabSalary Slip` ss
#         WHERE
#             ss.payroll_entry = %s
#                 AND ss.docstatus = 1
#         GROUP BY ss.payroll_entry
#         """,
#         (payroll_entry,),
#         as_dict=True,
#     )
#     if salary:
#         return salary[0]

#     default_result = frappe._dict(
#         {
#             "loan": 0,
#             "gross_pay": 0,
#             "net_pay": 0,
#             "tax_amount": 0,
#             "tax_regular": 0,
#             "tax_iregular": 0,
#             "count_employee": 0,
#         }
#     )
#     return default_result


# def _get_count_employee(payroll_entry):
#     count_employee = frappe.db.sql(
#         """
#         SELECT
#             COUNT(employee) AS count_employee
#         FROM
#             `tabSalary Slip` ss
#         WHERE
#             ss.payroll_entry = %s
#                 AND ss.docstatus = 1
#         GROUP BY ss.payroll_entry
#         """,
#         (payroll_entry,),
#         as_dict=True,
#     )
#     if count_employee:
#         return count_employee[0]["count_employee"]

#     return 0


# def _prepare_doc(data):
#     writer = UnicodeWriter()
#     earning_header = _get_salary_component(earning=True)
#     deduction_header = _get_salary_component(earning=False)
#     writer = _add_header(writer, earning_header, deduction_header)
#     writer = _add_data(writer, earning_header, deduction_header, data)

#     return writer


# def _get_salary_component(earning=True):
#     components = frappe.db.sql(
#         """
#         SELECT
#             sc.name AS name
#         FROM
#             `tabSalary Component` sc
#         WHERE
#             sc.disabled = 0
#                 AND sc.type = '{}'
#         ORDER BY sc.name
#         """.format(
#             "Earning" if earning else "Deduction"
#         ),
#         as_dict=True,
#     )
#     return [i["name"] for i in components]


# def _add_header(writer, earning_header, deduction_header):
#     row = []
#     row.append([_("Company")])
#     row.append([""])

#     row[0].append("Earnings")
#     first = True
#     for i in earning_header:
#         row[1].append(i)
#         if not first:
#             row[0].append("")
#         else:
#             first = False

#     row[0].append("Deductions")
#     first = True
#     for i in deduction_header:
#         row[1].append(i)
#         if not first:
#             row[0].append("")
#         else:
#             first = False

#     row[0].append("Tax")
#     first = True
#     for i in ("Tax Amount", ):
#         row[1].append(i)
#         if not first:
#             row[0].append("")
#         else:
#             first = False

#     row[0] = row[0] + [
#         _("Loan"),
#         _("Gross Salary"),
#         _("Net Salary"),
#         _("Employee Last Month"),
#         _("Employee Now"),
#         _("Employee Difference"),
#     ]
#     row[1] = row[1] + ["" for i in range(6)]

#     for r in row:
#         writer.writerow(r)
#     return writer


# def _get_header_list(earning_header, deduction_header):
#     row = []
#     row.append([_("Company")])
#     row.append([""])

#     header_list = []

#     row[0].append("Earnings")
#     first = True
#     for i in earning_header:
#         row[1].append(i)
#         if not first:
#             row[0].append("")
#         else:
#             first = False

#     row[0].append("Deductions")
#     first = True
#     for i in deduction_header:
#         row[1].append(i)
#         if not first:
#             row[0].append("")
#         else:
#             first = False

#     row[0].append("Tax")
#     first = True
#     for i in ("Tax Amount", ):
#         row[1].append(i)
#         if not first:
#             row[0].append("")
#         else:
#             first = False

#     row[0] = row[0] + [
#         _("Loan"),
#         _("Gross Salary"),
#         _("Net Salary"),
#         _("Employee Last Month"),
#         _("Employee Now"),
#         _("Employee Difference"),
#     ]
#     row[1] = row[1] + ["" for i in range(6)]

#     for r in row:
#         header_list.append(r)
#     return header_list


# def _add_data(writer, earning_header, deduction_header, data):
#     sorted_company = _sorted_data_list(data)
#     for company in sorted_company:
#         row = []
#         value = data[company]
#         row.append(value["company"])
#         for i in earning_header:
#             earning = value["earnings"]
#             row.append(earning.get(i, 0))
#         for i in deduction_header:
#             deduction = value["deductions"]
#             row.append(deduction.get(i, 0))
#         for i in ("Tax Amount", ):
#             taxes = value["tax"]
#             row.append(taxes.get(i, 0))
#         row.append(value["loan"])
#         row.append(value["gross_salary"])
#         row.append(value["net_salary"])
#         row.append(value["employee_last_month"])
#         row.append(value["employee_now"])
#         row.append(value["employee_difference"])
#         writer.writerow(row)
#     return writer


# def _get_data_list(earning_header, deduction_header, data):
#     sorted_company = _sorted_data_list(data)
#     data_list = []
#     for company in sorted_company:
#         row = []
#         value = data[company]
#         row.append(value["company"])
#         for i in earning_header:
#             earning = value["earnings"]
#             row.append(earning.get(i, 0))
#         for i in deduction_header:
#             deduction = value["deductions"]
#             row.append(deduction.get(i, 0))
#         for i in ("Tax Amount", ):
#             taxes = value["tax"]
#             row.append(taxes.get(i, 0))
#         row.append(value["loan"])
#         row.append(value["gross_salary"])
#         row.append(value["net_salary"])
#         row.append(value["employee_last_month"])
#         row.append(value["employee_now"])
#         row.append(value["employee_difference"])
#         data_list.append(row)
#     return data_list


# def _sorted_data_list(data):
#     return sorted(data, key=lambda k: k[0])
