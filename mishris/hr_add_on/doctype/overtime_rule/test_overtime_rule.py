# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from random import random
import datetime


def preparation(r_str=None):
    r_str = r_str if r_str else str(random())
    prep_doc = {}

    # company 1
    company = frappe.new_doc("Company")
    company.company_name = f"Test Company 1 {r_str}"
    company.abbr = f"TC{r_str[-4:]}"
    company.default_currency = "IDR"
    company.save()
    prep_doc["company1"] = frappe.get_doc("Company", company.name)
    # company 2
    company = frappe.new_doc("Company")
    company.company_name = f"Test Company 2 {r_str}"
    company.abbr = f"TC2{r_str[-4:]}"
    company.default_currency = "IDR"
    company.save()
    prep_doc["company2"] = frappe.get_doc("Company", company.name)

    # overtime bracket 1 from company 1
    overtime_bracket = frappe.new_doc("Overtime Bracket")
    overtime_bracket.bracket_name = f"Test Bracket 1-1 {r_str}"
    overtime_bracket.formula = "overtime_rate"
    overtime_bracket.company = prep_doc["company1"].name
    overtime_bracket.save()
    prep_doc["bracket1-1"] = frappe.get_doc("Overtime Bracket", overtime_bracket.name)
    # overtime bracket 2 from company 1
    overtime_bracket = frappe.new_doc("Overtime Bracket")
    overtime_bracket.bracket_name = f"Test Bracket 1-2 {r_str}"
    overtime_bracket.formula = "overtime_rate * 2"
    overtime_bracket.company = prep_doc["company1"].name
    overtime_bracket.save()
    prep_doc["bracket1-2"] = frappe.get_doc("Overtime Bracket", overtime_bracket.name)
    # overtime bracket 1 from company 2
    overtime_bracket = frappe.new_doc("Overtime Bracket")
    overtime_bracket.bracket_name = f"Test Bracket 2-1 {r_str}"
    overtime_bracket.formula = "overtime_rate"
    overtime_bracket.company = prep_doc["company2"].name
    overtime_bracket.save()
    prep_doc["bracket2-1"] = frappe.get_doc("Overtime Bracket", overtime_bracket.name)

    return prep_doc


def cleaning_up(prep_doc):
    # delete brackets
    for i in prep_doc:
        frappe.delete_doc_if_exists(prep_doc[i].doctype, prep_doc[i].name, force=1)


class TestOvertimeRule(unittest.TestCase):
    def setUp(self):
        self.r_str = str(random())
        self.prep_doc = preparation(self.r_str)

    def tearDown(self):
        cleaning_up(self.prep_doc)

    def test_create(self):
        overtime_rule = frappe.new_doc("Overtime Rule")
        overtime_rule.overtime_rule_name = f"Test Overtime Rule {self.r_str}"
        overtime_rule.company = self.prep_doc["company1"].name
        overtime_rule.applicable_on_holiday = 1
        overtime_rule.overtime_rate_formula = "base / 173"

        overtime_rule.append(
            "overtime_rule_list",
            {"time": "01:00", "bracket": self.prep_doc["bracket1-1"].name},
        )
        overtime_rule.save()

        # assert overtime rule name
        self.assertTrue(overtime_rule.name)
        result = frappe.get_doc("Overtime Rule", overtime_rule.name)
        # assert doc contains correct data
        self.assertEqual(f"Test Overtime Rule {self.r_str}", result.overtime_rule_name)
        self.assertEqual(self.prep_doc["company1"].name, result.company)
        self.assertEqual(1, result.applicable_on_holiday)
        self.assertEqual("base / 173", result.overtime_rate_formula)
        self.assertEqual(1, len(result.overtime_rule_list))
        self.assertEqual(
            datetime.timedelta(0, 3600), result.overtime_rule_list[0].time
        )  # datetime.timedelta(0, 3600) is representation of time 01:00
        self.assertEqual(
            self.prep_doc["bracket1-1"].name, result.overtime_rule_list[0].bracket
        )
        self.assertEqual(
            self.prep_doc["bracket1-1"].formula, result.overtime_rule_list[0].formula
        )
        frappe.delete_doc_if_exists("Overtime Rule", result.name, force=1)

    def test_validate_bracket_company(self):
        overtime_rule = frappe.new_doc("Overtime Rule")
        overtime_rule.overtime_rule_name = f"Test Overtime Rule {self.r_str}"
        overtime_rule.company = self.prep_doc["company1"].name
        overtime_rule.applicable_on_holiday = 1
        overtime_rule.overtime_rate_formula = "base / 173"

        overtime_rule.append(
            "overtime_rule_list",
            {"time": "01:00", "bracket": self.prep_doc["bracket2-1"].name},
        )

        with self.assertRaises(frappe.ValidationError):
            overtime_rule.save()
        frappe.delete_doc_if_exists("Overtime Rule", overtime_rule.name, force=1)

    def test_sort_rule_list(self):
        overtime_rule = frappe.new_doc("Overtime Rule")
        overtime_rule.overtime_rule_name = f"Test Overtime Rule {self.r_str}"
        overtime_rule.company = self.prep_doc["company1"].name
        overtime_rule.applicable_on_holiday = 1
        overtime_rule.overtime_rate_formula = "base / 173"

        overtime_rule.append(
            "overtime_rule_list",
            {"time": "08:00", "bracket": self.prep_doc["bracket1-2"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "04:00", "bracket": self.prep_doc["bracket1-1"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "02:00", "bracket": self.prep_doc["bracket1-1"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "03:00", "bracket": self.prep_doc["bracket1-1"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "05:00", "bracket": self.prep_doc["bracket1-2"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "06:00", "bracket": self.prep_doc["bracket1-2"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "01:00", "bracket": self.prep_doc["bracket1-1"].name},
        )
        overtime_rule.append(
            "overtime_rule_list",
            {"time": "07:00", "bracket": self.prep_doc["bracket1-2"].name},
        )
        overtime_rule.save()

        result = frappe.get_doc("Overtime Rule", overtime_rule.name)
        time_list = [(t.time.seconds / 3600.0) for t in result.overtime_rule_list]
        self.assertListEqual([1, 2, 3, 4, 5, 6, 7, 8], time_list)
        frappe.delete_doc_if_exists("Overtime Rule", result.name, force=1)
