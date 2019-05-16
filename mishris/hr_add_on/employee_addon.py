from __future__ import unicode_literals
import frappe
from datetime import datetime


def employee_nip(doc, event):
    if not doc.nip:
        noseries = doc.name.split("/")
        spliting = (noseries[-1])
        datetimeobject = datetime.strptime(
            str(doc.date_of_joining), '%Y-%m-%d')
        newformat = datetimeobject.strftime('%Y%m%d')
        doc.nip = newformat+spliting
        frappe.db.sql(
            """update `tabEmployee` set nip=%s where name=%s""", (doc.nip, doc.name))

def bank_name(doc, event):
	doc.bank_name = doc.bank