# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
import random

from frappe import ValidationError


def preparation(r_str=None):
    r_str = r_str or random.random()
    prep_doc = {}

    # create employee
    employee = frappe.new_doc("Employee")
    employee.first_name = "Test Employee {}".format(r_str)
    employee.gender = "Male"
    employee.date_of_birth = "1992-12-11"
    employee.date_of_joining = "2019-2-1"
    employee.save()
    prep_doc["employee"] = frappe.get_doc("Employee", employee.name)

    # create attendance status
    att_status_present = frappe.new_doc("Attendance Status")
    att_status_present.status_name = "Test Present {}".format(r_str)
    att_status_present.save()
    prep_doc["attendance_status_present"] = frappe.get_doc(
        "Attendance Status", att_status_present.name
    )

    # create attendance shift
    shift = frappe.new_doc("Attendance Shift")
    shift.shift_name = "Test Shift {}".format(r_str)
    shift.start_time = "08:00"
    shift.end_time = "17:00"
    shift.append(
        "shift_rule_list",
        {"condition": "check_in", "attendance_status": att_status_present.name},
    )
    shift.save()
    shift.submit()
    prep_doc["attendance_shift"] = frappe.get_doc("Attendance Shift", shift.name)

    return prep_doc


class TestAttendanceShiftAssignment(unittest.TestCase):
    def setUp(self):
        self.r_str = random.random()
        prep_doc = preparation(self.r_str)

        # create employee
        self.employee = prep_doc["employee"]

        # create attendance status
        self.att_status_present = prep_doc["attendance_status_present"]

        # create attendance shift
        self.shift = prep_doc["attendance_shift"]

    def tearDown(self):
        self.shift.cancel()
        self.shift.delete()
        self.att_status_present.delete()
        self.employee.delete()

    def test_create_attendance_shift_assignment(self):
        # create shift assignment
        s_asg = frappe.new_doc("Attendance Shift Assignment")
        s_asg.employee = self.employee.name
        s_asg.attendance_shift = self.shift.name
        s_asg.from_date = "2019-2-4"
        s_asg.save()
        s_asg.submit()
        # assert
        self.assertFalse(not s_asg.name)
        doc = frappe.get_doc("Attendance Shift Assignment", s_asg.name)
        self.assertEqual(doc.docstatus, 1)
        # delete doc
        doc.cancel()
        doc.delete()

    def test_validate_shift_submitted_raise_exception(self):
        # Create attendance status draft
        att_status_draft = frappe.new_doc("Attendance Status")
        att_status_draft.status_name = "Test Draft {}".format(self.r_str)
        att_status_draft.save()
        # create attendance shift draft
        shift = frappe.new_doc("Attendance Shift")
        shift.shift_name = "Test Shift Draft {}".format(self.r_str)
        shift.start_time = "08:00"
        shift.end_time = "17:00"
        shift.append(
            "shift_rule_list",
            {"condition": "check_in", "attendance_status": att_status_draft.name},
        )
        shift.save()

        with self.assertRaises(ValidationError):
            s_asg = frappe.new_doc("Attendance Shift Assignment")
            s_asg.employee = self.employee.name
            s_asg.attendance_shift = shift.name
            s_asg.from_date = "2019-2-8"
            s_asg.save()
            # should catch the exception on save,
            # but in case it passed, cancel and delete doc
            s_asg.submit()
            s_asg.cancel()
            s_asg.delete()
        # delete doc
        shift.delete()
        att_status_draft.delete()
