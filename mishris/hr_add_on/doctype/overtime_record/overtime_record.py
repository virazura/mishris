# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe import _
from frappe.model.document import Document

from mishris.hr_add_on.doctype.overtime_application.overtime_application import (
    combine_date_time_to_str,
)


class NoCheckOutError(frappe.ValidationError):
    pass


class OvertimeRecord(Document):
    def validate(self):
        self.calculate_overtime_and_details()
        self.calculate_total_amount()

    def calculate_overtime_and_details(self):
        overtime_application = frappe.get_doc(
            "Overtime Application", self.overtime_application
        )
        attendance = frappe.get_doc("Attendance", self.attendance)
        overtime_and_details = get_overtime_and_details(
            attendance, overtime_application, calculate_amount=True
        )
        self.overtime = overtime_and_details["overtime"]
        details = overtime_and_details["overtime_detail"]
        self.overtime_detail = []
        for det in details:
            self.append("overtime_detail", det)

    def calculate_total_amount(self):
        self.total_amount = 0
        for detail in self.overtime_detail:
            self.total_amount += detail.amount


def create_overtime_record(attendance_doc, method):
    # ! Do Not create overtime record if did not have overtime application
    if not attendance_doc.overtime_application:
        return

    overtime_record = frappe.new_doc("Overtime Record")
    overtime_record.employee = attendance_doc.employee
    overtime_record.overtime_application = attendance_doc.overtime_application
    overtime_record.overtime_rule = frappe.get_value(
        "Overtime Application", attendance_doc.overtime_application, "overtime_rule"
    )
    overtime_record.attendance = attendance_doc.name
    overtime_record.attendance_date = attendance_doc.attendance_date
    overtime_record.attendance_shift = attendance_doc.attendance_shift
    overtime_record.flags.ignore_permissions = 1
    overtime_record.save()
    overtime_record.submit()


def calculate_overtime(attendance_doc, overtime_application_doc):
    if not attendance_doc.check_out:
        frappe.throw(
            _("Check Out is mandatory for calculate overtime"), exc=NoCheckOutError
        )
    if overtime_application_doc.is_holiday:
        start_overtime = combine_date_time_to_str(
            attendance_doc.attendance_date, attendance_doc.check_in, as_datetime=True
        )
    else:
        end_shift = frappe.get_value(
            "Attendance Shift", attendance_doc.attendance_shift, "end_time"
        )
        start_overtime = combine_date_time_to_str(
            attendance_doc.attendance_date, end_shift, as_datetime=True
        )
    end_overtime = combine_date_time_to_str(
        attendance_doc.check_out_date, attendance_doc.check_out, as_datetime=True
    )

    overtime = end_overtime - start_overtime
    return overtime


def get_overtime_and_details(
    attendance_doc, overtime_application_doc=None, calculate_amount=False
):
    result = {"overtime": datetime.timedelta(0), "overtime_detail": []}

    if (not overtime_application_doc) and attendance_doc.overtime_application:
        overtime_application_doc = frappe.get_doc(
            "Overtime Application", attendance_doc.overtime_application
        )
    elif (not overtime_application_doc) and (not attendance_doc.overtime_application):
        return result

    employee = frappe.get_all(
        "Employee",
        filters={"name": overtime_application_doc.employee},
        fields=["name", "get_overtime_bonus"],
    )[0]

    if calculate_amount and employee.get_overtime_bonus:
        overtime_rate = _eval_base_overtime_rate(
            overtime_application_doc.employee,
            overtime_application_doc.overtime_date,
            overtime_application_doc.overtime_rule,
        )
    else:
        overtime_rate = 0

    overtime = calculate_overtime(attendance_doc, overtime_application_doc)
    result["overtime"] = overtime

    overtime_rule = frappe.get_doc(
        "Overtime Rule", overtime_application_doc.overtime_rule
    )
    overtime_rule_list_sorted = sorted(
        overtime_rule.overtime_rule_list, key=(lambda k: k.time)
    )

    details = {}
    before = datetime.timedelta(0)
    for rule in overtime_rule_list_sorted:
        if overtime >= rule.time:
            if calculate_amount and employee.get_overtime_bonus:
                base_amount = _eval_overtime_amount(overtime_rate, rule.bracket)
            else:
                base_amount = 0

            if rule.bracket in details:
                details[rule.bracket]["overtime"] += rule.time - before
                details[rule.bracket]["amount"] += base_amount
            else:
                details[rule.bracket] = {
                    "bracket": rule.bracket,
                    "overtime": (rule.time - before),
                    "amount": base_amount,
                }
            before = rule.time
        else:
            break

    for key, val in details.items():
        result["overtime_detail"].append(val)

    return result


def _get_employee_salary_structure_assignment_data(employee, overtime_date):
    data = frappe._dict()
    salary_structure_assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": employee,
            "docstatus": 1,
            "from_date": ["<=", overtime_date],
        },
        order_by="from_date desc",
        limit_page_length=1,
        fields=["base", "variable"],
    )
    if salary_structure_assignments:
        data["base"] = salary_structure_assignments[0]["base"]
        data["variable"] = salary_structure_assignments[0]["variable"]
    else:
        frappe.throw(
            _("Salary Structure Assignment for Employee {} not found").format(employee)
        )
    return data


def _eval_base_overtime_rate(employee, overtime_date, overtime_rule):
    whitelisted_globals = {"int": int, "float": float, "long": int, "round": round}
    data = _get_employee_salary_structure_assignment_data(employee, overtime_date)

    overtime_rule = frappe.get_all(
        "Overtime Rule",
        filters={"name": overtime_rule},
        limit_page_length=1,
        fields=["*"],
    )[0]
    overtime_rate_formula = overtime_rule.overtime_rate_formula
    overtime_rate = frappe.safe_eval(overtime_rate_formula, whitelisted_globals, data)
    return overtime_rate


def _eval_overtime_amount(overtime_rate, overtime_bracket):
    whitelisted_globals = {"int": int, "float": float, "long": int, "round": round}

    data = frappe._dict()
    data["overtime_rate"] = overtime_rate

    overtime_bracket = frappe.get_all(
        "Overtime Bracket",
        filters={"name": overtime_bracket},
        limit_page_length=1,
        fields=["*"],
    )[0]
    formula = overtime_bracket.formula

    amount = frappe.safe_eval(formula, whitelisted_globals, data)
    return amount


@frappe.whitelist()
def get_total_amount(employee, from_date, to_date):
    """get total overtime amount in chosen date range for employee
    API access method:
        'mishris.hr_add_on.doctype.overtime_record.overtime_record.get_total_amount'
    :param employee: name of employee (str)
    :param from_date: date (str in format YYYY-MM-DD)
    :param to_date: date (str in format YYYY-MM-DD)
    :return: total amount (int for used in currency format)
    """
    result = frappe.db.sql(
        "SELECT SUM(total_amount) as total_amount from `tabOvertime Record` "
        "where attendance_date >= %s and attendance_date <= %s and employee = %s;",
        (from_date, to_date, employee),
        as_dict=True,
    )
    if result and len(result) > 0:
        return result[0].total_amount or 0
    return 0
