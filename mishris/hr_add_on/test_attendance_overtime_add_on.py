from __future__ import unicode_literals

import datetime
import random
import unittest

import frappe
from mishris.hr_add_on.doctype.overtime_application.test_overtime_application import (
    preparation as toa_preparation,
)


def preparation(r_str=None):
    r_str = r_str or str(random.random())
    prep_doc = {**toa_preparation(r_str)}

    overtime_application = frappe.new_doc("Overtime Application")
    overtime_application.employee = prep_doc["employee1"].name
    overtime_application.company = prep_doc["company1"].name
    overtime_application.overtime_rule = prep_doc["overtime_rule"].name
    overtime_application.overtime_date = "2019-02-20"
    overtime_application.start_overtime = "17:00"
    overtime_application.end_date = "2019-02-20"
    overtime_application.end_overtime = "21:00"
    overtime_application.save()
    overtime_application.submit()
    prep_doc["overtime_application"] = frappe.get_doc(
        "Overtime Application", overtime_application.name
    )

    overtime_application = frappe.new_doc("Overtime Application")
    overtime_application.employee = prep_doc["employee1"].name
    overtime_application.company = prep_doc["company1"].name
    overtime_application.overtime_rule = prep_doc["overtime_rule"].name
    overtime_application.overtime_date = "2019-02-23"
    overtime_application.start_overtime = "09:00"
    overtime_application.end_date = "2019-02-23"
    overtime_application.end_overtime = "16:00"
    overtime_application.save()
    overtime_application.submit()
    prep_doc["overtime_application_holiday"] = frappe.get_doc(
        "Overtime Application", overtime_application.name
    )

    # Create shift assignment
    shift_asg = frappe.new_doc("Attendance Shift Assignment")
    shift_asg.employee = prep_doc["employee1"].name
    shift_asg.attendance_shift = prep_doc["attendance_shift"].name
    shift_asg.from_date = "2019-2-4"
    shift_asg.save()
    shift_asg.submit()
    prep_doc["attendance_shift_assignment"] = frappe.get_doc(
        "Attendance Shift Assignment", shift_asg.name
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


class TestAttendanceOvertimeAddOn(unittest.TestCase):
    def setUp(self):
        self.r_str = str(random.random())
        self.prep_doc = preparation(self.r_str)
        self.prep_doc["employee1"].get_overtime_bonus = 0
        self.prep_doc["employee1"].save()
        self.prep_doc["employee2"].get_overtime_bonus = 0
        self.prep_doc["employee2"].save()

    def tearDown(self):
        cleaning_up(self.prep_doc)

    def create_doc(self, **kwargs):
        fields = {
            "employee": self.prep_doc["employee1"].name,
            "company": self.prep_doc["company1"].name,
            "attendance_date": "2019-02-20",
            "check_in": "07:55",
            "check_out_date": "2019-02-20",
            "check_out": "18:02",
        }
        fields.update(kwargs)

        attendance = frappe.new_doc("Attendance")
        attendance.employee = fields["employee"]
        attendance.company = fields["company"]
        attendance.attendance_date = fields["attendance_date"]
        attendance.check_in = fields["check_in"]
        attendance.check_out_date = fields["check_out_date"]
        attendance.check_out = fields["check_out"]
        attendance.save()
        attendance.submit()

        return frappe.get_doc("Attendance", attendance.name)

    def delete_doc(self, doc):
        overtime_records = frappe.get_all("Overtime Record", filters={
            "attendance": doc.name
        })
        for r in overtime_records:
            rec = frappe.get_doc("Overtime Record", r)
            if rec.docstatus == 1:
                rec.cancel()
            frappe.delete_doc_if_exists("Overtime Record", r, force=1)
        doc.cancel()
        frappe.delete_doc_if_exists("Attendance", doc.name, force=1)

    def test_get_overtime_application(self):
        doc = self.create_doc()

        self.assertEqual(
            self.prep_doc["overtime_application"].name, doc.overtime_application
        )

        self.delete_doc(doc)

    def test_employee_do_not_have_overtime_application(self):
        doc = self.create_doc(employee=self.prep_doc["employee2"].name)
        self.assertIsNone(doc.overtime_application)
        self.delete_doc(doc)

    def test_overtime_total_check_out_as_end_overtime(self):
        doc = self.create_doc(check_out="21:00")
        self.assertEqual(doc.overtime, datetime.timedelta(0, (3600 * 4)))
        self.delete_doc(doc)

    def test_overtime_total_check_out_before_end_overtime(self):
        doc = self.create_doc(check_out="20:00")
        self.assertEqual(doc.overtime, datetime.timedelta(0, (3600 * 3)))
        self.delete_doc(doc)

    def test_overtime_total_check_out_after_end_overtime(self):
        doc = self.create_doc(check_out="23:00")
        self.assertEqual(doc.overtime, datetime.timedelta(0, (3600 * 6)))
        self.delete_doc(doc)

    def test_overtime_total_holiday(self):
        doc = self.create_doc(
            attendance_date="2019-02-23",
            check_in="09:00",
            check_out_date="2019-02-23",
            check_out="16:00",
        )
        self.assertEqual(doc.overtime, datetime.timedelta(0, (3600 * 7)))
        self.delete_doc(doc)

    def test_overtime_detail(self):
        doc = self.create_doc(check_in="08:00", check_out="21:00")

        overtime_detail = doc.overtime_detail
        self.assertTrue(overtime_detail)
        self.assertEqual(len(doc.overtime_detail), 2)
        details = []
        for i in overtime_detail:
            details.append(
                {"bracket": i.bracket, "overtime": i.overtime, "amount": i.amount}
            )
        expected_details = [
            {
                "bracket": self.prep_doc["bracket1-1"].name,
                "overtime": datetime.timedelta(0, (3600 * 2)),
                "amount": 0,
            },
            {
                "bracket": self.prep_doc["bracket1-2"].name,
                "overtime": datetime.timedelta(0, (3600 * 2)),
                "amount": 0,
            },
        ]
        self.assertCountEqual(expected_details, details)

        self.delete_doc(doc)
