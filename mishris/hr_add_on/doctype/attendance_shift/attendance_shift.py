# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document


class AttendanceShift(Document):
    @frappe.whitelist()
    def assign_attendance_shift(
        self,
        grade=None,
        department=None,
        designation=None,
        employee=None,
        from_date=None,
    ):
        employees = self.get_employees(
            grade=grade, department=department, designation=designation, name=employee
        )
        # assign attendance shift
        if employees:
            if len(employees) > 20:
                frappe.enqueue(
                    assign_attendance_shift_for_employee,
                    timeout=600,
                    employees=employees,
                    attendance_shift=self,
                    from_date=from_date,
                )
            else:
                assign_attendance_shift_for_employee(
                    employees, self, from_date=from_date
                )
        else:
            frappe.msgprint(_("No Employee Found"))

    def get_employees(self, **kwargs):
        conditions, values = [], []
        for field, value in kwargs.items():
            if value:
                conditions.append("{0}=%s".format(field))
                values.append(value)
        condition_str = " and " + " and ".join(conditions) if conditions else ""

        employees = frappe.db.sql_list(
            "select name from tabEmployee "
            "where status='Active'{condition}".format(condition=condition_str),
            tuple(values),
        )
        return employees


def assign_attendance_shift_for_employee(employees, attendance_shift, from_date=None):
    attendance_shift_assignments = []
    count = 0
    for employee in employees:
        count += 1

        assignment = create_attendance_shift_assignment(
            employee, attendance_shift, from_date
        )
        attendance_shift_assignments.append(assignment)
        frappe.publish_progress(
            count * 100 / len(employees), title=_("Assigning Attendance Shift")
        )
    if attendance_shift_assignments:
        frappe.msgprint(_("Structures have been assigned successfully"))


def create_attendance_shift_assignment(employee, attendance_shift, from_date):
    assignment = frappe.new_doc("Attendance Shift Assignment")
    assignment.employee = employee
    assignment.attendance_shift = attendance_shift.name
    assignment.from_date = from_date
    assignment.save(ignore_permissions=True)
    assignment.submit()
    return assignment.name
