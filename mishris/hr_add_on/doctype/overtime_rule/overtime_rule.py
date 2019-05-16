# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document


class OvertimeRuleNotApplicableOnHolidayError(frappe.ValidationError):
    pass


class OvertimeRule(Document):
    def validate(self):
        self.sort_rule_list()
        self.validate_bracket_company()

    def validate_bracket_company(self):
        for row in self.overtime_rule_list:
            bracket_company = frappe.get_value(
                "Overtime Bracket", row.bracket, "company"
            )
            if bracket_company != self.company:
                frappe.throw(_("Incorrect Company for Bracket {}").format(row.bracket))

    def sort_rule_list(self, desc=False):
        """sort rule list by time"""
        self.overtime_rule_list.sort(key=(lambda k: k.time), reverse=desc)
        for i in range(len(self.overtime_rule_list)):
            self.overtime_rule_list[i].idx = i + 1
