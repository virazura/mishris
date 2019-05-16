from __future__ import unicode_literals

import datetime
import random
import unittest

import frappe
from frappe.exceptions import ValidationError
from mishris.hr_add_on.attendance_add_on import (
    eval_condition_and_status,
    get_attendance_data,
)


def prepare_attendance():
    r_str = random.random()

    # Create Employee
    new_emp = frappe.new_doc("Employee")
    new_emp.first_name = "Test Employee {}".format(r_str)
    new_emp.gender = "Male"
    new_emp.date_of_birth = "1992-12-11"
    new_emp.date_of_joining = "2019-2-1"
    new_emp.save()

    # Create Attendance Status
    att_status_present = frappe.new_doc("Attendance Status")
    att_status_present.status_name = "Test Present {}".format(r_str)
    att_status_present.save()

    att_status_late = frappe.new_doc("Attendance Status")
    att_status_late.status_name = "Test Late {}".format(r_str)
    att_status_late.save()

    # Create Shift rule
    shift = frappe.new_doc("Attendance Shift")
    shift.shift_name = "Test Shift {}".format(r_str)
    shift.start_time = "08:00"
    shift.end_time = "17:00"
    shift.append(
        "shift_rule_list",
        {"condition": "check_in", "attendance_status": att_status_present.name},
    )
    shift.append(
        "shift_rule_list",
        {
            "condition": "check_in > start_time",
            "attendance_status": att_status_late.name,
        },
    )
    shift.save()
    shift.submit()

    # Create shift assignment
    shift_asg = frappe.new_doc("Attendance Shift Assignment")
    shift_asg.employee = new_emp.name
    shift_asg.attendance_shift = shift.name
    shift_asg.from_date = "2019-2-4"
    shift_asg.save()
    shift_asg.submit()

    # Create Attendance Present
    attendance = frappe.new_doc("Attendance")
    attendance.employee = new_emp.name
    attendance.attendance_date = "2019-02-13"
    attendance.check_in = "08:45"
    attendance.check_out = "17:02"
    attendance.save()
    attendance.submit()

    return {
        "employee": new_emp,
        "attendance_status_present": att_status_present,
        "attendance_status_late": att_status_late,
        "attendance_shift": shift,
        "attendance_shift_assignment": shift_asg,
        "attendance": attendance,
    }


def tear_down_attendance(preparation_doc):
    preparation_doc["attendance"].cancel()
    preparation_doc["attendance"].delete()
    preparation_doc["attendance_shift_assignment"].cancel()
    preparation_doc["attendance_shift_assignment"].delete()
    preparation_doc["attendance_shift"].cancel()
    preparation_doc["attendance_shift"].delete()
    preparation_doc["attendance_status_late"].delete()
    preparation_doc["attendance_status_present"].delete()
    preparation_doc["employee"].delete()


class TestAttendanceAddOn(unittest.TestCase):
    def setUp(self):
        self.prep_doc = prepare_attendance()

    def tearDown(self):
        tear_down_attendance(self.prep_doc)

    def test_update_attendance_shift(self):
        self.assertEqual(
            self.prep_doc["attendance"].attendance_shift,
            self.prep_doc["attendance_shift"].name,
        )

    def test_update_attendance_shift_not_found(self):
        with self.assertRaises(ValidationError):
            attendance = frappe.new_doc("Attendance")
            attendance.employee = self.prep_doc["employee"].name
            attendance.attendance_date = "2019-02-1"
            attendance.check_in = "07:45"
            attendance.check_out = "17:02"
            attendance.save()

    def test_get_attendance_data(self):
        attendance = frappe.get_doc("Attendance", self.prep_doc["attendance"].name)
        attendance_shift = frappe.get_doc(
            "Attendance Shift", self.prep_doc["attendance_shift"].name
        )
        employee = frappe.get_doc("Employee", self.prep_doc["employee"].name)
        data_result = get_attendance_data(attendance)
        self.assertEqual(data_result.attendance_date, attendance.attendance_date)
        self.assertIsInstance(data_result.check_in, datetime.time)
        self.assertEqual(data_result.first_name, employee.first_name)
        self.assertEqual(data_result.shift_name, attendance_shift.shift_name)
        self.assertFalse(data_result.on_leave)

    def test_update_default_status(self):
        attendance_present = frappe.get_doc(
            "Attendance", self.prep_doc["attendance"].name
        )
        self.assertEqual(attendance_present.status, "Present")

    def test_update_attendance_status(self):
        attendance = frappe.get_doc("Attendance", self.prep_doc["attendance"].name)
        expect_status_name = [
            self.prep_doc["attendance_status_late"].name,
            self.prep_doc["attendance_status_present"].name,
        ]
        for i in attendance.attendance_status_list:
            self.assertIn(i.attendance_status, expect_status_name)
        self.assertEqual(
            attendance.attendance_status_summary, ", ".join(sorted(expect_status_name))
        )

    def test_eval_condition_and_status(self):
        attendance = frappe.get_doc("Attendance", self.prep_doc["attendance"].name)
        data = get_attendance_data(attendance)
        method_result = eval_condition_and_status(attendance, data)
        self.assertCountEqual(
            method_result,
            [
                self.prep_doc["attendance_status_late"].name,
                self.prep_doc["attendance_status_present"].name,
            ],
        )
