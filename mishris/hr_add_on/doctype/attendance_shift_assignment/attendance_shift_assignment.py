# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today


class AttendanceShiftNotFoundError(frappe.ValidationError):
    pass


class AttendanceShiftAssignment(Document):
    def validate(self):
        self.validate_shift_submitted()

    def validate_shift_submitted(self):
        shift = frappe.get_doc("Attendance Shift", self.attendance_shift)
        if shift.docstatus != 1:
            frappe.throw(
                _("Attendance Shift {} must be submitted").format(shift.name),
                title=_("Invalid Attendance Shift"),
            )


def get_attendance_shift(employee, date=None):
    if not date:
        date = today()

    attendance_shift_assignment = frappe.get_all(
        "Attendance Shift Assignment",
        filters=[
            ["employee", "=", employee],
            ["from_date", "<=", date],
            ["docstatus", "=", 1],
        ],
        fields=["name", "employee", "attendance_shift", "from_date"],
        order_by="from_date desc",
        limit_page_length=1,
    )
    if len(attendance_shift_assignment) > 0:
        return attendance_shift_assignment[0].attendance_shift
    else:
        frappe.throw(
            _("Attendance Shift not found for {}").format(employee),
            exc=AttendanceShiftNotFoundError,
        )
