from __future__ import unicode_literals

import frappe
from erpnext.hr.doctype.upload_attendance.upload_attendance import (
    get_active_employees, get_dates, get_naming_series)
from frappe import _
from frappe.utils import cstr, getdate
from frappe.utils.csvutils import UnicodeWriter


@frappe.whitelist()
def download_template():
    if not frappe.has_permission("Attendance", "create"):
        raise frappe.PermissionError
    args = frappe.local.form_dict

    w = UnicodeWriter()
    w = add_header(w)

    w = add_data(w, args)

    frappe.response['result'] = cstr(w.getvalue())
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Attendance"


def add_header(w):
    row = [
        ["Notes:"],
        ["Please do not change the template headings"],
        ["Status will automatically updated based on employee shift rule"],
        ["If you are overwriting existing attendance records, "
            "'ID' column is mandatory"],
        [
            "ID", "Employee", "Company", "Naming Series",
            "Attendance Date", "Check In", "Check Out Date", "Check Out"
        ]
    ]
    for r in row:
        w.writerow(r)
    return w


def add_data(w, args):
    data = get_data(args)
    for row in data:
        w.writerow(row)
    return w


def get_data(args):
    dates = get_dates(args)
    employees = get_active_employees()
    existing_attendance_records = get_existing_attendance_records(args)
    data = []
    for date in dates:
        for employee in employees:
            if getdate(date) < getdate(employee.date_of_joining):
                continue
            if employee.relieving_date:
                if getdate(date) > getdate(employee.relieving_date):
                    continue
            existing_attendance = {}
            if (existing_attendance_records and
                    tuple([getdate(date), employee.name]) in
                    existing_attendance_records and
                    getdate(employee.date_of_joining) >= getdate(date) and
                    getdate(employee.relieving_date) <= getdate(date)):
                existing_attendance = existing_attendance_records[
                    tuple([getdate(date), employee.name])]
            row = [
                existing_attendance and existing_attendance.name or "",
                employee.name,
                employee.company,
                (existing_attendance and existing_attendance.naming_series or
                    get_naming_series()),
                date,
                existing_attendance and existing_attendance.check_in or "",
                existing_attendance and existing_attendance.check_out or ""
            ]
            data.append(row)
    return data


def get_existing_attendance_records(args):
    attendance = frappe.db.sql("""select name, attendance_date, employee,
        status, leave_type, naming_series, check_in, check_out, check_out_date
        from `tabAttendance` where attendance_date between %s and %s and
        docstatus < 2""", (args["from_date"], args["to_date"]), as_dict=1)

    existing_attendance = {}
    for att in attendance:
        existing_attendance[tuple([att.attendance_date, att.employee])] = att

    return existing_attendance


@frappe.whitelist()
def upload():
    if not frappe.has_permission("Attendance", "create"):
        raise frappe.PermissionError

    from frappe.utils.csvutils import read_csv_content_from_uploaded_file
    from frappe.modules import scrub

    rows = read_csv_content_from_uploaded_file()
    rows = list(filter(lambda x: x and any(x), rows))
    if not rows:
        msg = [_("Please select a csv file")]
        return {"messages": msg, "error": msg}
    columns = [scrub(f) for f in rows[4]]
    columns[0] = "name"
    ret = []
    error = False

    from frappe.utils.csvutils import check_record, import_doc

    for i, row in enumerate(rows[5:]):
        if not row:
            continue
        row_idx = i + 5
        doc = frappe._dict(zip(columns, row))
        doc["doctype"] = "Attendance"
        if doc.name:
            doc["docstatus"] = frappe.db.get_value(
                    "Attendance", doc.name, "docstatus")

        try:
            check_record(doc)
            ret.append(import_doc(doc, "Attendance", 1, row_idx, submit=True))
        except AttributeError:
            pass
        except Exception as exc:
            error = True
            ret.append("Error for row ({}) {} : {}".format(
                row_idx, (len(row) > 1 and row[1] or ""), cstr(exc)))

        if error:
            frappe.db.rollback()
        else:
            frappe.db.commit()
    return {"messages": ret, "error": error}
