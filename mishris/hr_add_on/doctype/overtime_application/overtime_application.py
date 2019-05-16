# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import datetime

import frappe
from erpnext.hr.doctype.employee.employee import is_holiday
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_datetime, getdate, time_diff, today
from mishris.hr_add_on.doctype.attendance_shift_assignment.attendance_shift_assignment import (
    get_attendance_shift,
)
from mishris.hr_add_on.doctype.overtime_rule.overtime_rule import (
    OvertimeRuleNotApplicableOnHolidayError,
)


class OvertimeInWorkingHoursError(frappe.ValidationError):
    pass


class MultipleApplicationInONeDayError(frappe.ValidationError):
    pass


class OvertimeApplication(Document):
    def get_total_overtime(self):
        start_datetime = combine_date_time_to_str(
            self.overtime_date, self.start_overtime
        )
        end_datetime = combine_date_time_to_str(self.end_date, self.end_overtime)
        return time_diff(end_datetime, start_datetime)

    def get_end_date(self):
        return self.end_date or self.overtime_date

    def update_missing_fields(self):
        self.attendance_shift = get_attendance_shift(self.employee, self.overtime_date)
        self.total_overtime = self.get_total_overtime()
        self.is_holiday = is_holiday(self.employee, self.overtime_date)

    def validate(self):
        self.validate_multiple_application_in_one_day()
        self.validate_end_date()

        self.update_missing_fields()

        self.validate_overtime_in_holiday()
        self.validate_overtime_in_working_hours()

    def validate_overtime_in_working_hours(self):
        # do not check overtime in working hours in holiday
        if self.is_holiday:
            return
        shift_doc = frappe.get_doc("Attendance Shift", self.attendance_shift)
        start_overtime = combine_date_time_to_str(
            self.overtime_date, self.start_overtime
        )
        end_overtime = combine_date_time_to_str(self.end_date, self.end_overtime)
        start_shift = combine_date_time_to_str(self.overtime_date, shift_doc.start_time)
        if shift_doc.end_time > shift_doc.start_time:
            end_shift = combine_date_time_to_str(self.overtime_date, shift_doc.end_time)
        else:
            end_shift = combine_date_time_to_str(
                add_days(self.overtime_date, 1), shift_doc.end_time
            )
        start_shift_next_day = combine_date_time_to_str(
            add_days(self.overtime_date, 1), shift_doc.start_time
        )

        if (
            ((start_overtime > start_shift) and (start_overtime < end_shift))
            or ((end_overtime > start_shift) and (end_overtime < end_shift))
            or (end_overtime > start_shift_next_day)
        ):
            frappe.throw(
                _(
                    "Overtime in working hours. "
                    "Shift from {} to {} but overtime from {} to {}"
                ).format(
                    shift_doc.start_time,
                    shift_doc.end_time,
                    self.start_overtime,
                    self.end_overtime,
                ),
                exc=OvertimeInWorkingHoursError,
            )

    def validate_overtime_in_holiday(self):
        overtime_rule = frappe.get_doc("Overtime Rule", self.overtime_rule)
        if self.is_holiday and not overtime_rule.applicable_on_holiday:
            frappe.throw(
                _("Overtime Rule is Not Applicable On Holiday"),
                exc=OvertimeRuleNotApplicableOnHolidayError,
            )

    def validate_end_date(self):
        def get_date(date):
            if isinstance(date, str):
                date = getdate(date)
            return date

        self.end_date = self.get_end_date()
        start_date = get_date(self.overtime_date)
        end_date = get_date(self.end_date)
        if end_date < start_date:
            frappe.throw(_("Invalid date for End Date"))

    def validate_multiple_application_in_one_day(self):
        doc = get_overtime_application(self.employee, self.overtime_date)
        if doc:
            frappe.throw(
                _("Multiple document in one day is not allowed"),
                exc=MultipleApplicationInONeDayError,
            )


def combine_date_time_to_str(date, time, as_datetime=False):
    def strtime(time):
        if isinstance(time, datetime.timedelta):
            return "{h:02n}:{m:02n}".format(
                h=time.total_seconds() // 3600, m=((time.total_seconds() % 3600) // 60)
            )
        else:
            return time

    def strdatetime(date, time):
        if isinstance(date, datetime.datetime):
            return "{} {}".format(date.strftime("%Y-%m-%d"), time)
        else:
            return "{} {}".format(date, time)

    datetime_str = strdatetime(date, strtime(time))
    return datetime_str if not as_datetime else get_datetime(datetime_str)


def get_overtime_application(employee, overtime_date=None, as_doc=False):
    overtime_date = overtime_date or today()
    docs = frappe.get_all(
        "Overtime Application",
        filters={"employee": employee, "overtime_date": overtime_date, "docstatus": 1},
    )
    if len(docs) > 0 and not as_doc:
        return docs[0]
    elif len(docs) > 0 and as_doc:
        return frappe.get_doc("Overtime Application", docs[0])
    else:
        return None
