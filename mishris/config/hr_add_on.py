from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Attendance"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Attendance Status"
                },
                {
                    "type": "doctype",
                    "name": "Attendance Shift"
                },
                {
                    "type": "doctype",
                    "name": "Attendance Shift Assignment"
                },
                {
                    "type": "doctype",
                    "name": "Attendance Change Request"
                },
                {
                    "type": "doctype",
                    "name": "Overtime Rule"
                },
                {
                    "type": "doctype",
                    "name": "Overtime Bracket"
                },
                {
                    "type": "doctype",
                    "name": "Overtime Application"
                },
                {
                    "type": "doctype",
                    "name": "Overtime Record"
                }
            ]
        },
        {
            "label": _("Employee & Insurance"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Employee Insurance Update"
                },
                {
                    "type": "doctype",
                    "name": "Insurance"
                },
                {
                    "type": "doctype",
                    "name": "Marital Status"
                },
                {
                    "type": "doctype",
                    "name": "Outsource"
                },
                {
                    "type": "doctype",
                    "name": "Religion"
                },
                {
                    "type": "doctype",
                    "name": "Dependant"
                },
                {
                    "type": "doctype",
                    "name": "Kartu Keluarga"
                }

            ]
        },
        {
            "label": _("Income Tax"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Employee Tax Income"
                },
                {
                    "type": "doctype",
                    "name": "Non Taxable Income"
                },
                {
                    "type": "doctype",
                    "name": "Tax Bracket"
                },
                {
                    "type": "doctype",
                    "name": "SPT 1721_A1"
                }
            ]
        },
        {
            "label": _("Report"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Payroll Summary Report"
                }
            ]
        }
    ]
