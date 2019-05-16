from __future__ import unicode_literals

import datetime

import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import get_time, getdate


def get_attendance_data(doc):
    data = frappe._dict()
    data.update(
        frappe.get_doc("Attendance Shift", doc.attendance_shift).as_dict()
    )
    data.update(frappe.get_doc("Employee", doc.employee).as_dict())
    data.update(doc.as_dict())

    # get if employee is on_leave / on_leave_half
    leave_application = frappe.get_all(
        "Leave Application",
        filters=[
            ['employee', '=', doc.employee],
            ['from_date', '<=', doc.attendance_date],
            ['to_date', '>=', doc.attendance_date],
            ['docstatus', '=', 1]
        ],
        fields=['name', 'half_day', 'half_day_date']
    )
    data['on_leave'] = len(leave_application) > 0
    data['on_leave_half'] = (
        data['on_leave'] and leave_application[0].half_day and
        leave_application[0].half_day_date == data.attendance_date
    )

    data = fix_data_type(data)
    return data


def fix_data_type(data):
    for key, value in data.items():
        # cast from datetime.timedelta to datetime.time
        if isinstance(value, datetime.timedelta):
            hour = value.seconds // 3600
            minute = (value.seconds % 3600) // 60
            second = ((value.seconds % 3600) % 60)
            data[key] = datetime.time(hour, minute, second)
        # cast check_in and check_out from str to datetime.time
        if key in ["check_in", "check_out"]:
            try:
                data[key] = get_time(value)
            except (ValueError, TypeError):
                data[key] = None
    return data


def eval_condition_and_status(doc, data):
    whitelisted_globals = {
        "int": int,
        "float": float,
        "long": int,
        "round": round,
        "date": datetime.date,
        "datetime": datetime.datetime,
        "time": datetime.time,
        "getdate": getdate,
        "gettime": get_time
    }

    shift = frappe.get_doc("Attendance Shift", doc.attendance_shift)
    shift_rule = shift.shift_rule_list

    status_rows = []
    for row in shift_rule:
        try:
            if frappe.safe_eval(row.condition, whitelisted_globals, data):
                status_rows.append(row.attendance_status)
        except TypeError:
            pass

    return status_rows


def update_attendance_status(doc, data):
    status_rows = eval_condition_and_status(doc, data)

    doc.attendance_status_list = []
    for status in status_rows:
        doc.append("attendance_status_list", {"attendance_status": status})

    doc.attendance_status_summary = ", ".join(sorted(status_rows))


def update_attendance_shift(doc):
    attendance_shift = frappe.get_all(
        "Attendance Shift Assignment",
        filters=[
            ["employee", '=', doc.employee],
            ["from_date", "<=", doc.attendance_date],
            ["docstatus", "=", 1]
        ],
        fields=['name', 'employee', 'attendance_shift', 'from_date'],
        order_by="from_date desc",
        limit_page_length=1
    )

    if len(attendance_shift) > 0:
        doc.attendance_shift = attendance_shift[0].attendance_shift
    else:
        frappe.throw(
            _("Attendance Shift not found for {}").format(doc.employee),
            exc=ValidationError
        )

    return doc


def update_check_out_date(doc):
    if not doc.check_out_date:
        doc.check_out_date = doc.attendance_date
    return doc


def update_default_status(doc, data):
    # default status
    if data.on_leave_half:
        doc.status = "Half Day"
    elif data.on_leave:
        doc.status = "On Leave"
    elif doc.check_in:
        doc.status = "Present"
    else:
        doc.status = "Absent"


def attendance_add_on(doc, method):
    update_attendance_shift(doc)
    update_check_out_date(doc)

    data = get_attendance_data(doc)

    update_default_status(doc, data)
    update_attendance_status(doc, data)
