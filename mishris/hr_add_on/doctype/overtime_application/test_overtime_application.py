# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and Contributors
# See license.txt
from __future__ import unicode_literals

import datetime
import unittest
from random import random

import frappe
from frappe.utils import getdate
from mishris.hr_add_on.doctype.attendance_shift_assignment.attendance_shift_assignment import (
    AttendanceShiftNotFoundError,
)
from mishris.hr_add_on.doctype.attendance_shift_assignment.test_attendance_shift_assignment import (
    preparation as asa_preparation,
)
from mishris.hr_add_on.doctype.overtime_application.overtime_application import (
    MultipleApplicationInONeDayError,
    OvertimeInWorkingHoursError,
    get_overtime_application,
)
from mishris.hr_add_on.doctype.overtime_rule.overtime_rule import (
    OvertimeRuleNotApplicableOnHolidayError,
)
from mishris.hr_add_on.doctype.overtime_rule.test_overtime_rule import (
    preparation as rule_preparation,
)


def preparation(r_str=None):
    r_str = r_str if r_str else str(random())
    prep_doc = {**rule_preparation(r_str), **asa_preparation(r_str)}

    # holiday list
    holiday_list = frappe.new_doc("Holiday List")
    holiday_list.holiday_list_name = f"Test Holiday List {r_str}"
    holiday_list.from_date = "2019-01-01"
    holiday_list.to_date = "2019-12-31"
    d_holiday = {
        "2019-02-02": "Saturday",
        "2019-02-03": "Sunday",
        "2019-02-09": "Saturday",
        "2019-02-10": "Sunday",
        "2019-02-16": "Saturday",
        "2019-02-17": "Sunday",
        "2019-02-23": "Saturday",
        "2019-02-24": "Sunday",
    }
    for dt, dy in d_holiday.items():
        holiday_list.append("holidays", {"holiday_date": dt, "description": dy})
    holiday_list.save()
    prep_doc["holiday_list"] = frappe.get_doc("Holiday List", holiday_list.name)

    # create overtime rule
    overtime_rule = frappe.new_doc("Overtime Rule")
    overtime_rule.overtime_rule_name = f"Test Overtime Rule {r_str}"
    overtime_rule.company = prep_doc["company1"].name
    overtime_rule.applicable_on_holiday = 1
    overtime_rule.overtime_rate_formula = "base / 173"
    brackets = {
        "01:00": "bracket1-1",
        "02:00": "bracket1-1",
        "03:00": "bracket1-2",
        "04:00": "bracket1-2",
    }
    for t, b in brackets.items():
        overtime_rule.append(
            "overtime_rule_list", {"time": t, "bracket": prep_doc[b].name}
        )
    overtime_rule.save()
    prep_doc["overtime_rule"] = frappe.get_doc("Overtime Rule", overtime_rule.name)

    # create employee
    for i, emp in {
        "employee1": {"name": f"Employee Bonus {r_str}", "bonus": 1},
        "employee2": {"name": f"Employee No Bonus {r_str}", "bonus": 0},
    }.items():
        employee = frappe.new_doc("Employee")
        employee.first_name = emp["name"]
        employee.company = prep_doc["company1"].name
        employee.gender = "Male"
        employee.date_of_birth = "1992-02-09"
        employee.date_of_joining = "2019-02-01"
        employee.get_overtime_bonus = emp["bonus"]
        employee.holiday_list = holiday_list.name
        employee.save()
        prep_doc[i] = frappe.get_doc("Employee", employee.name)

    # attendance shift assignment
    for i in ("employee1", "employee2"):
        attendance_shift_assignment = frappe.new_doc("Attendance Shift Assignment")
        attendance_shift_assignment.employee = prep_doc[i].name
        attendance_shift_assignment.attendance_shift = prep_doc["attendance_shift"].name
        attendance_shift_assignment.from_date = "2019-2-1"
        attendance_shift_assignment.save()
        attendance_shift_assignment.submit()
        prep_doc[f"attendance_shift_assignment_{i}"] = frappe.get_doc(
            "Attendance Shift Assignment", attendance_shift_assignment.name
        )

    return prep_doc


def cleaning_up(prep_doc):
    while prep_doc:
        poplist = []
        for i in prep_doc:
            try:
                if prep_doc[i].docstatus == 1:
                    prep_doc[i].cancel()
                frappe.delete_doc_if_exists(
                    prep_doc[i].doctype, prep_doc[i].name, force=1
                )
                poplist.append(i)
            except frappe.exceptions.LinkExistsError:
                pass
        for i in poplist:
            prep_doc.pop(i)


class TestOvertimeApplication(unittest.TestCase):
    def setUp(self):
        self.r_str = str(random())
        self.prep_doc = preparation(self.r_str)

    def tearDown(self):
        cleaning_up(self.prep_doc)

    def create_doc(self, **kwargs):
        fields = {
            "employee": self.prep_doc["employee1"].name,
            "company": self.prep_doc["company1"].name,
            "overtime_rule": self.prep_doc["overtime_rule"].name,
            "overtime_date": "2019-02-20",
            "start_overtime": "17:00",
            "end_date": "2019-02-20",
            "end_overtime": "21:00",
        }
        fields.update(kwargs)

        overtime_application = frappe.new_doc("Overtime Application")
        overtime_application.employee = fields["employee"]
        overtime_application.company = fields["company"]
        overtime_application.overtime_rule = fields["overtime_rule"]
        overtime_application.overtime_date = fields["overtime_date"]
        overtime_application.start_overtime = fields["start_overtime"]
        overtime_application.end_date = fields["end_date"]
        overtime_application.end_overtime = fields["end_overtime"]
        overtime_application.save()
        overtime_application.submit()

        return frappe.get_doc("Overtime Application", overtime_application.name)

    def delete_doc(self, doc):
        doc.cancel()
        frappe.delete_doc_if_exists("Overtime Application", doc.name, force=1)

    def test_create(self):
        result = self.create_doc()

        self.assertEqual(self.prep_doc["employee1"].name, result.employee)
        self.assertEqual(self.prep_doc["employee1"].employee_name, result.employee_name)
        self.assertEqual(self.prep_doc["employee1"].department, result.department)
        self.assertEqual(self.prep_doc["company1"].name, result.company)
        self.assertEqual(self.prep_doc["overtime_rule"].name, result.overtime_rule)
        self.assertEqual(getdate("2019-02-20"), result.overtime_date)
        self.assertEqual(getdate("2019-02-20"), result.end_date)
        self.assertEqual(datetime.timedelta(0, (3600 * 17)), result.start_overtime)
        self.assertEqual(datetime.timedelta(0, (3600 * 21)), result.end_overtime)
        self.assertEqual(
            datetime.timedelta(0, (3600 * (21 - 17))), result.total_overtime
        )
        self.assertEqual(
            self.prep_doc["attendance_shift"].name, result.attendance_shift
        )
        self.assertFalse(result.is_holiday)

        self.delete_doc(result)

    def test_holiday_check(self):
        result = self.create_doc(overtime_date="2019-02-23", end_date="2019-02-23")

        self.assertTrue(result.is_holiday)

        self.delete_doc(result)

    def test_different_date(self):
        result = self.create_doc(
            overtime_date="2019-02-20",
            start_overtime="21:00",
            end_date="2019-02-21",
            end_overtime="05:00",
        )

        self.assertEqual(datetime.timedelta(0, (3600 * 8)), result.total_overtime)

        self.delete_doc(result)

    def test_employee_attendance_shift_not_found(self):
        employee = frappe.new_doc("Employee")
        employee.first_name = f"Employee No Attendance Assignment {self.r_str}"
        employee.company = self.prep_doc["company1"].name
        employee.gender = "Male"
        employee.date_of_birth = "1992-02-09"
        employee.date_of_joining = "2019-02-01"
        employee.get_overtime_bonus = 1
        employee.holiday_list = self.prep_doc["holiday_list"].name
        employee.save()

        with self.assertRaises(AttendanceShiftNotFoundError):
            result = self.create_doc(employee=employee.name)
            self.delete_doc(result)

    def test_overtime_in_working_hours_forbidden_case_start_time(self):
        with self.assertRaises(OvertimeInWorkingHoursError):
            result = self.create_doc(start_overtime="15:00")
            self.delete_doc(result)

    def test_overtime_in_working_hours_forbidden_case_end_time(self):
        with self.assertRaises(OvertimeInWorkingHoursError):
            result = self.create_doc(start_overtime="05:00", end_overtime="09:00")
            self.delete_doc(result)

    def test_overtime_in_working_hours_forbidden_case_start_end_time(self):
        with self.assertRaises(OvertimeInWorkingHoursError):
            result = self.create_doc(start_overtime="09:00", end_overtime="14:00")
            self.delete_doc(result)

    def test_overtime_in_working_hours_forbidden_case_start_end_time_cross_day(self):
        with self.assertRaises(OvertimeInWorkingHoursError):
            result = self.create_doc(
                overtime_date="2019-02-20",
                start_overtime="23:00",
                end_date="2019-02-21",
                end_overtime="09:00",
            )
            self.delete_doc(result)

    def test_overtime_in_working_hours_allowed_in_holiday(self):
        result = self.create_doc(
            overtime_date="2019-02-23",
            start_overtime="09:00",
            end_date="2019-02-23",
            end_overtime="15:00",
        )
        self.assertTrue(result.name)
        self.assertTrue(result.is_holiday)
        self.delete_doc(result)

    def test_end_date_before_start_date_error(self):
        with self.assertRaises(frappe.ValidationError):
            result = self.create_doc(overtime_date="2019-02-20", end_date="2019-02-19")
            self.delete_doc(result)

    def test_get_overtime_application(self):
        doc = self.create_doc()
        result = get_overtime_application(doc.employee, doc.overtime_date)

        self.assertEqual(result.name, doc.name)

        self.delete_doc(doc)

    def test_multiple_docs_in_one_day_error(self):
        doc1 = self.create_doc()
        with self.assertRaises(MultipleApplicationInONeDayError):
            doc2 = self.create_doc()
            self.delete_doc(doc2)
        self.delete_doc(doc1)

    def test_overtime_not_applicable_for_holiday(self):
        self.prep_doc["overtime_rule"].applicable_on_holiday = 0
        self.prep_doc["overtime_rule"].save()

        with self.assertRaises(OvertimeRuleNotApplicableOnHolidayError):
            result = self.create_doc(overtime_date="2019-02-23", end_date="2019-02-23")
            self.delete_doc(result)
