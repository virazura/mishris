from __future__ import unicode_literals
import frappe


def get_context(context):
    context.employee = frappe.get_list("Employee", fields=["employee_name", "designation"])
    


        
