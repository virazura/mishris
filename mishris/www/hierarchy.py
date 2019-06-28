from __future__ import unicode_literals
import frappe
import json


def get_context(context):
    employee_data = frappe.get_list("Employee", fields=["employee_name", "designation", "employee_name_for_report"])
    context["employee_data"] = json.dumps(employee_data)

    
    
    


        
