# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class WrongAttendanceError(frappe.ValidationError):
    pass


class WrongAttendanceStatusError(frappe.ValidationError):
    pass


class WrongAttendanceDateError(frappe.ValidationError):
    pass


class AttendanceChangeRequest(Document):
    def validate(self):
        self.validate_attendance_documents()
        self.validate_request_date()

    def validate_request_date(self):
        if getdate(self.attendance_date) > getdate():
            frappe.throw(
                _("Cannot choose future date for Attendance Date"),
                exc=WrongAttendanceDateError,
            )
        pass

    def validate_attendance_status(self, new_attendance):
        """Validate new_attendance must be submitted
        """
        if new_attendance.docstatus != 1:
            frappe.throw(
                _("Attendance status for {} must be Submitted").format(
                    self.new_attendance
                ),
                exc=WrongAttendanceStatusError,
            )

    def validate_attendance_employee(self, new_attendance):
        """Validate new_attendance must have the same employee as this document
        """
        if new_attendance.employee != self.employee:
            frappe.throw(
                _("Wrong attendance document {} for employee {}").format(
                    self.new_attendance, self.employee
                ),
                exc=WrongAttendanceError,
            )

    def validate_attendance_date(self, new_attendance):
        """Validate new_attendance must have the same attendance_date as
        this document
        """
        if new_attendance.attendance_date != getdate(self.attendance_date):
            frappe.throw(
                _("Wrong attendance date for {}").format(self.new_attendance),
                exc=WrongAttendanceDateError,
            )

    def validate_new_attendance_ammended(self, new_attendance):
        if not new_attendance.amended_from:
            frappe.throw(
                _(
                    "New attendance document {} must be " "amended from old attendance"
                ).format(self.new_attendance),
                exc=WrongAttendanceError,
            )

    def validate_attendance_documents(self):
        """Validate new_attendance documents
        """
        if self.new_attendance:
            attendance = frappe.get_doc("Attendance", self.new_attendance)
            self.validate_attendance_status(attendance)
            self.validate_attendance_employee(attendance)
            self.validate_attendance_date(attendance)


@frappe.whitelist()
def get_attendance_approver(employee, department=None):
    if not department:
        department = frappe.db.get_value("Employee", employee, "department")

    if department:
        return frappe.db.get_value(
            "Attendance Department Approver",
            {"parent": department, "parentfield": "attendance_approvers", "idx": 1},
            "approver",
        )
