# Copyright (c) 2013, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import add_days, cstr, get_first_day, get_last_day, get_time, getdate
from frappe.utils.csvutils import UnicodeWriter


def execute(filters=None):
    from_date, to_date = get_date(filters)
    list_of_date = get_list_of_date(from_date, to_date)
    list_of_status = get_list_of_status()

    columns = get_columns(from_date, to_date, list_of_date, list_of_status)
    data = get_data(from_date, to_date, columns, list_of_date, list_of_status)

    return columns, data


@frappe.whitelist()
def download_report():
    args = frappe.local.form_dict
    from_date = args["from_date"]
    to_date = args["to_date"]
    list_of_date = get_list_of_date(from_date, to_date)
    list_of_status = get_list_of_status()
    data_dict = get_data_dict(from_date, to_date)
    writer = _prepare_doc(data_dict, list_of_date, list_of_status)

    frappe.response["result"] = cstr(writer.getvalue())
    frappe.response["type"] = "csv"
    frappe.response["doctype"] = "Attendance Summary Report {} - {}".format(
        from_date, to_date
    )


def _prepare_doc(data_dict, list_of_date, list_of_status):
    writer = UnicodeWriter()
    writer = _add_header(writer, list_of_date, list_of_status)
    writer = _add_data(writer, data_dict, list_of_date, list_of_status)
    return writer


def _add_header(writer, list_of_date, list_of_status):
    row = [[], []]

    for i in ("Employee", "Employee Name", "Company"):
        row[0].append(i)
        row[1].append("")

    first = True
    for i in list_of_date:
        row[0].append(i)
        row[1].append("Check In")
        row[0].append("")
        row[1].append("Check Out")
        first = not first

    first = True
    for i in list_of_status:
        if first:
            row[0].append("Attendance Status Summary")
            first = False
        else:
            row[0].append("")
        row[1].append(i)

    for r in row:
        writer.writerow(r)
    return writer


def _add_data(writer, data_dict, list_of_date, list_of_status):
    for key, dd in data_dict.items():
        row = [dd["name"], dd["employee_name"], dd["company"]]

        for date in list_of_date:
            try:
                row.append(dd["attendance"][str(date)]["check_in"])
                row.append(dd["attendance"][str(date)]["check_out"])
            except KeyError:
                row.append(None)
                row.append(None)

        for status in list_of_status:
            try:
                row.append(dd["attendance_status_summary"][status])
            except KeyError:
                row.append(0)

        writer.writerow(row)
    return writer


def get_date(filters=None):
    from_date = None
    to_date = None

    if filters:
        from_date = getdate(filters.from_date)
        to_date = getdate(filters.to_date)

    if not from_date:
        from_date = get_first_day(getdate())
    if not to_date:
        to_date = get_last_day(from_date)

    return (from_date, to_date)


def get_columns(from_date, to_date, list_of_date, list_of_status):
    columns = [_("Employee"), _("Employee Name"), _("Company")]
    for d in list_of_date:
        for s in (_("Check In"), _("Check Out")):
            columns.append(d.strftime("%d-%m-%Y {}".format(s)))
    for s in list_of_status:
        columns.append(s)
    return columns


def get_list_of_date(from_date, to_date):
    list_of_date = []
    d = from_date
    while d <= to_date:
        list_of_date.append(d)
        d = add_days(d, 1)
    return list_of_date


def get_list_of_status():
    status_raw = frappe.get_list("Attendance Status", order_by="name")
    status = [s["name"] for s in status_raw]
    return status


def get_data(from_date, to_date, columns, list_of_date, list_of_status):
    data_dict = get_data_dict(from_date, to_date)
    data = data_dict_to_data_list(data_dict, list_of_date, list_of_status)
    return data


def get_data_dict(from_date, to_date):
    data_dict = {}

    employees = get_employees(from_date, to_date)
    data_dict = data_dict_add_employees(employees, data_dict)

    attendances = get_attendance(from_date, to_date)
    data_dict = data_dict_add_attendance(attendances, data_dict)

    summary_status = get_summary_status(from_date, to_date)
    data_dict = data_dict_add_summary_status(summary_status, data_dict)

    return data_dict


def get_employees(from_date, to_date):
    query = _get_employees_query(from_date, to_date)
    employees = frappe.db.sql(query[0], query[1], as_dict=True)
    return employees


def _get_employees_query(from_date, to_date, name_only=False):
    return (
        """
        SELECT
            {}
        FROM
            `tabEmployee`
        WHERE
            date_of_joining <= %s
                AND (status = 'Active'
                OR relieving_date >= %s)
        ORDER BY company , name
        """.format(
            "name, employee_name, company" if not name_only else "name"
        ),
        (to_date, from_date),
    )


def data_dict_add_employees(employees, data_dict=None):
    if not data_dict:
        data_dict = {}
    for emp in employees:
        data_dict[emp["name"]] = emp
    return data_dict


def get_attendance(from_date, to_date):
    emp_query = _get_employees_query(from_date, to_date, name_only=True)

    attendances = frappe.db.sql(
        """
        SELECT
            att.employee,
            att.attendance_date,
            att.check_out_date,
            att.check_in,
            att.check_out
        FROM
            `tabAttendance` att
        WHERE
            att.attendance_date >= %s
                AND att.attendance_date <= %s
                AND att.docstatus = 1
                AND att.employee in ({})
        ORDER BY att.attendance_date , att.employee
        """.format(
            emp_query[0]
        ),
        (from_date, to_date, *emp_query[1]),
        as_dict=True,
    )
    return attendances


def data_dict_add_attendance(attendances, data_dict):
    """Add attendance to data dict,
    to be run after data_dict_add_employees

    :param attendances: list of dict attendance data
    [
        {
            "employee": str employee name,
            "attendance_date": str date,
            "check_in": str time,
            "check_out": str time
        }
    ]
    :param data_dict: dict of data

    :returns: data_dict
    """
    for att in attendances:
        emp_name = att["employee"]
        emp_data = data_dict[emp_name]
        att_date = att["attendance_date"]

        if not emp_data.get("attendance"):
            data_dict[emp_name]["attendance"] = {}

        data_dict[emp_name]["attendance"][str(att_date)] = {
            "check_in": str(get_time(att["check_in"])) if att["check_in"] else None,
            "check_out": str(get_time(att["check_out"])) if att["check_out"] else None,
        }
    return data_dict


def get_summary_status(from_date, to_date):
    emp_query = _get_employees_query(from_date, to_date, name_only=True)

    summary_status = frappe.db.sql(
        """
        SELECT
            att.employee,
            asl.attendance_status,
            COUNT(asl.attendance_status) AS attendance_status_count
        FROM
            `tabAttendance Status List` asl
                JOIN
            `tabAttendance` att ON (att.name = asl.parent)
        WHERE
            att.attendance_date >= %s
                AND att.attendance_date <= %s
                AND att.employee in ({})
        GROUP BY att.employee, asl.attendance_status
        """.format(
            emp_query[0]
        ),
        (from_date, to_date, *emp_query[1]),
        as_dict=True,
    )
    return summary_status


def data_dict_add_summary_status(summary_status, data_dict):
    for ss in summary_status:
        emp_name = ss["employee"]
        data = data_dict[emp_name]

        if not data.get("attendance_status_summary"):
            data_dict[emp_name]["attendance_status_summary"] = {}

        data_dict[emp_name]["attendance_status_summary"][ss["attendance_status"]] = ss[
            "attendance_status_count"
        ]
    return data_dict


def data_dict_to_data_list(data_dict, list_of_date, list_of_status):
    data_list = []
    for key, dd in data_dict.items():
        data = [dd["name"], dd["employee_name"], dd["company"]]

        for date in list_of_date:
            try:
                data.append(dd["attendance"][str(date)]["check_in"])
                data.append(dd["attendance"][str(date)]["check_out"])
            except KeyError:
                data.append(None)
                data.append(None)

        for i in list_of_status:
            try:
                data.append(dd["attendance_status_summary"][i])
            except KeyError:
                data.append(0)

        data_list.append(data)
    return data_list
