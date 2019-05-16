from __future__ import unicode_literals

import frappe
from mishris.hr_add_on.doctype.overtime_application.overtime_application import (
    get_overtime_application,
)
from mishris.hr_add_on.doctype.overtime_record.overtime_record import (
    get_overtime_and_details,
)


def update_overtime(doc):
    overtime_application = get_overtime_application(
        doc.employee, doc.attendance_date, as_doc=True
    )
    if overtime_application:
        doc.overtime_application = overtime_application.name
        overtime_and_records = get_overtime_and_details(doc, overtime_application)

        doc.overtime = overtime_and_records["overtime"]
        doc.overtime_detail = []
        for det in overtime_and_records["overtime_detail"]:
            doc.append("overtime_detail", det)
    return doc


def attendance_overtime_add_on(doc, method):
    update_overtime(doc)
