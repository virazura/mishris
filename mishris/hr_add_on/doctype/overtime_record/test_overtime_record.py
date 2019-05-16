# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
import random
import datetime

from mishris.hr_add_on.test_attendance_overtime_add_on import (
    preparation as tao_preparation,
    cleaning_up,
)
from mishris.hr_add_on.doctype.overtime_record.overtime_record import get_total_amount


def preparation(r_str=None):
    r_str = r_str or str(random.random())
    prep_doc = {**tao_preparation(r_str)}

    salary_structure = frappe.new_doc("Salary Structure")
    salary_structure.__newname = f"Test Salary Structure {r_str}"
    salary_structure.name = f"Test Salary Structure {r_str}"
    salary_structure.is_actice = "Yes"
    salary_structure.company = prep_doc["company1"].name
    salary_structure.save()
    salary_structure.submit()
    prep_doc["salary_structure"] = frappe.get_doc(
        "Salary Structure", salary_structure.name
    )

    salary_assign = frappe.new_doc("Salary Structure Assignment")
    salary_assign.employee = prep_doc["employee1"].name
    salary_assign.company = prep_doc["company1"].name
    salary_assign.salary_structure = prep_doc["salary_structure"].name
    salary_assign.from_date = prep_doc["employee1"].date_of_joining
    salary_assign.base = 1_730_000
    salary_assign.save()
    salary_assign.submit()
    prep_doc["salary_structure_assignment"] = frappe.get_doc(
        "Salary Structure Assignment", salary_assign.name
    )

    return prep_doc


class TestOvertimeRecord(unittest.TestCase):
    def setUp(self):
        self.r_str = str(random.random())
        self.prep_doc = preparation(self.r_str)

    def tearDown(self):
        cleaning_up(self.prep_doc)
        # pass

    def create_attendance_doc(self, **kwargs):
        fields = {
            "employee": self.prep_doc["employee1"].name,
            "company": self.prep_doc["company1"].name,
            "attendance_date": "2019-02-20",
            "check_in": "08:00",
            "check_out_date": "2019-02-20",
            "check_out": "21:00",
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

    def delete_attendance_doc(self, attendance_doc):
        attendance_doc.cancel()
        frappe.delete_doc_if_exists("Attendance", attendance_doc.name, force=1)

    def test_create_overtime_records_on_attendance_submit(self):
        attendance_doc = self.create_attendance_doc()

        overtime_records = frappe.get_all(
            "Overtime Record",
            filters={"attendance": attendance_doc.name, "docstatus": 1},
        )
        self.assertTrue(len(overtime_records) == 1)

        overtime_record = frappe.get_doc("Overtime Record", overtime_records[0].name)
        self.assertTrue(overtime_record.name)

        self.assertEqual(overtime_record.employee, self.prep_doc["employee1"].name)
        self.assertEqual(
            overtime_record.overtime_rule, self.prep_doc["overtime_rule"].name
        )
        self.assertEqual(
            overtime_record.overtime_application,
            self.prep_doc["overtime_application"].name,
        )
        self.assertEqual(overtime_record.attendance, attendance_doc.name)
        self.assertEqual(
            overtime_record.attendance_date, attendance_doc.attendance_date
        )
        self.assertEqual(
            overtime_record.attendance_shift, attendance_doc.attendance_shift
        )

        overtime_record.cancel()
        frappe.delete_doc_if_exists("Overtime Record", overtime_record.name)
        self.delete_attendance_doc(attendance_doc)

    def test_overtime(self):
        attendance_doc = self.create_attendance_doc()
        overtime_records = frappe.get_all(
            "Overtime Record",
            filters={"attendance": attendance_doc.name, "docstatus": 1},
        )
        overtime_record = frappe.get_doc("Overtime Record", overtime_records[0].name)

        self.assertEqual(overtime_record.overtime, datetime.timedelta(0, (3600 * 4)))

        overtime_record.cancel()
        frappe.delete_doc_if_exists("Overtime Record", overtime_record.name)
        self.delete_attendance_doc(attendance_doc)

    def test_overtime_no_salary_assignment(self):
        self.prep_doc["salary_structure_assignment"].cancel()
        with self.assertRaises(frappe.ValidationError):
            attendance_doc = self.create_attendance_doc()
            overtime_records = frappe.get_all(
                "Overtime Record",
                filters={"attendance": attendance_doc.name, "docstatus": 1},
            )
            overtime_record = frappe.get_doc("Overtime Record", overtime_records[0].name)
            overtime_record.cancel()
            frappe.delete_doc_if_exists("Overtime Record", overtime_record.name)
            self.delete_attendance_doc(attendance_doc)

    def test_overtime_detail(self):
        attendance_doc = self.create_attendance_doc()
        overtime_records = frappe.get_all(
            "Overtime Record",
            filters={"attendance": attendance_doc.name, "docstatus": 1},
        )
        overtime_record = frappe.get_doc("Overtime Record", overtime_records[0].name)
        overtime_detail = overtime_record.overtime_detail

        self.assertTrue(overtime_detail)
        self.assertEqual(len(overtime_detail), 2)

        expected_details = [
            {
                "bracket": self.prep_doc["bracket1-1"].name,
                "overtime": datetime.timedelta(0, (3600 * 2)),
                "amount": 20000,
            },
            {
                "bracket": self.prep_doc["bracket1-2"].name,
                "overtime": datetime.timedelta(0, (3600 * 2)),
                "amount": 40000,
            },
        ]
        details = []
        for det in overtime_detail:
            details.append(
                {"bracket": det.bracket, "overtime": det.overtime, "amount": det.amount}
            )

        self.assertCountEqual(expected_details, details)

        overtime_record.cancel()
        frappe.delete_doc_if_exists("Overtime Record", overtime_record.name)
        self.delete_attendance_doc(attendance_doc)

    def test_overtime_detail_no_overtime_bonus(self):
        self.prep_doc["employee1"].get_overtime_bonus = 0
        self.prep_doc["employee1"].save()

        attendance_doc = self.create_attendance_doc()
        overtime_records = frappe.get_all(
            "Overtime Record",
            filters={"attendance": attendance_doc.name, "docstatus": 1},
        )
        overtime_record = frappe.get_doc("Overtime Record", overtime_records[0].name)
        overtime_detail = overtime_record.overtime_detail

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
        details = []
        for det in overtime_detail:
            details.append(
                {"bracket": det.bracket, "overtime": det.overtime, "amount": det.amount}
            )

        self.assertCountEqual(expected_details, details)

        overtime_record.cancel()
        frappe.delete_doc_if_exists("Overtime Record", overtime_record.name)
        self.delete_attendance_doc(attendance_doc)

    def test_total_amount(self):
        attendance_doc = self.create_attendance_doc()
        overtime_records = frappe.get_all(
            "Overtime Record",
            filters={"attendance": attendance_doc.name, "docstatus": 1},
        )
        overtime_record = frappe.get_doc("Overtime Record", overtime_records[0].name)

        self.assertEqual(60000, overtime_record.total_amount)

        overtime_record.cancel()
        frappe.delete_doc_if_exists("Overtime Record", overtime_record.name)
        self.delete_attendance_doc(attendance_doc)


class TestOvertimeRecords(unittest.TestCase):
    def setUp(self):
        self.r_str = str(random.random())
        self.prep_doc = {**tao_preparation(self.r_str)}

        self.from_date = "2019-2-25"
        self.to_date = "2019-2-27"

        salary_structure = frappe.new_doc("Salary Structure")
        salary_structure.__newname = f"Test Salary Structure {self.r_str}"
        salary_structure.name = f"Test Salary Structure {self.r_str}"
        salary_structure.is_actice = "Yes"
        salary_structure.company = self.prep_doc["company1"].name
        salary_structure.save()
        salary_structure.submit()
        self.prep_doc["salary_structure"] = frappe.get_doc(
            "Salary Structure", salary_structure.name
        )

        salary_assign = frappe.new_doc("Salary Structure Assignment")
        salary_assign.employee = self.prep_doc["employee1"].name
        salary_assign.company = self.prep_doc["company1"].name
        salary_assign.salary_structure = self.prep_doc["salary_structure"].name
        salary_assign.from_date = self.prep_doc["employee1"].date_of_joining
        salary_assign.base = 1_730_000
        salary_assign.save()
        salary_assign.submit()
        self.prep_doc["salary_structure_assignment"] = frappe.get_doc(
            "Salary Structure Assignment", salary_assign.name
        )

        self.overtime_application = []
        for i in range(25, 28):
            overtime_application = frappe.new_doc("Overtime Application")
            overtime_application.employee = self.prep_doc["employee1"].name
            overtime_application.company = self.prep_doc["company1"].name
            overtime_application.overtime_rule = self.prep_doc["overtime_rule"].name
            overtime_application.overtime_date = f"2019-02-{i}"
            overtime_application.start_overtime = "17:00"
            overtime_application.end_date = f"2019-02-{i}"
            overtime_application.end_overtime = "21:00"
            overtime_application.save()
            overtime_application.submit()
            self.overtime_application.append(
                frappe.get_doc("Overtime Application", overtime_application.name)
            )

        self.attendance = []
        for i in range(25, 28):
            attendance = frappe.new_doc("Attendance")
            attendance.employee = self.prep_doc["employee1"].name
            attendance.company = self.prep_doc["company1"].name
            attendance.attendance_date = f"2019-02-{i}"
            attendance.check_in = "08:00"
            attendance.check_out_date = f"2019-02-{i}"
            attendance.check_out = "21:00"
            attendance.save()
            attendance.submit()
            self.attendance.append(frappe.get_doc("Attendance", attendance.name))

    def tearDown(self):
        overtime_records = frappe.get_all(
            "Overtime Record", filters={"employee": self.prep_doc["employee1"].name}
        )
        for dname in overtime_records:
            doc = frappe.get_doc("Overtime Record", dname.name)
            doc.cancel()
            frappe.delete_doc_if_exists(doc.doctype, doc.name, force=1)
        while self.prep_doc:
            poplist = []
            for i in self.prep_doc:
                try:
                    if self.prep_doc[i].docstatus == 1:
                        self.prep_doc[i].cancel()
                    frappe.delete_doc_if_exists(
                        self.prep_doc[i].doctype, self.prep_doc[i].name, force=1
                    )
                    poplist.append(i)
                except frappe.exceptions.LinkExistsError:
                    pass
            for i in poplist:
                self.prep_doc.pop(i)
        for doc in self.attendance:
            doc.cancel()
            frappe.delete_doc_if_exists(doc.doctype, doc.name, force=1)
        for doc in self.overtime_application:
            doc.cancel()
            frappe.delete_doc_if_exists(doc.doctype, doc.name, force=1)

    def test_get_total_amount_employee_from_date_to_date(self):
        employee = self.prep_doc["employee1"]
        from_date = self.from_date
        to_date = self.to_date
        amount = get_total_amount(employee.name, from_date, to_date)
        self.assertEqual(amount, 180_000)
