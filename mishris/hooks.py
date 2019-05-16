# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "mishris"
app_title = "MIS HRIS"
app_publisher = "MIS"
app_description = "MIS Human Resource Information System"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "mis@misgroup.id"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mishris/css/mishris.css"
# app_include_js = "/assets/mishris/js/mishris.js"

# include js, css files in header of web template
# web_include_css = "/assets/mishris/css/mishris.css"
# web_include_js = "/assets/mishris/js/mishris.js"
web_include_js = ["assets/js/libs.min.js"]

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype": "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
doctype_js = {"Upload Attendance": "public/js/upload_attendance_add_on.js"}
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"
home_page = "dashboard"

# website user home page (by Role)
# role_home_page = {
#     "Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "mishris.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "mishris.install.before_install"
# after_install = "mishris.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mishris.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#     "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
doc_events = {
    "Attendance": {
        "validate": [
            "mishris.hr_add_on.attendance_add_on.attendance_add_on",
            "mishris.hr_add_on.attendance_overtime_add_on.attendance_overtime_add_on",
        ],
        "on_submit": "mishris.hr_add_on.doctype.overtime_record.overtime_record.create_overtime_record",
    },
    "Employee": {
        "on_update": "mishris.hr_add_on.employee_addon.employee_nip",
        "validate": "mishris.hr_add_on.employee_addon.bank_name",
    },
    "Salary Slip": {
        "validate": "mishris.hr_add_on.salary_slip_addon.salary_slip_detail"
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#     "all": [
#         "mishris.tasks.all"
#     ],
#     "daily": [
#         "mishris.tasks.daily"
#     ],
#     "hourly": [
#         "mishris.tasks.hourly"
#     ],
#     "weekly": [
#         "mishris.tasks.weekly"
#     ]
#     "monthly": [
#         "mishris.tasks.monthly"
#     ]
# }

# Testing
# -------

# before_tests = "mishris.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
#    "frappe.desk.doctype.event.event.get_events": "mishris.event.get_events"
# }

# Fixtures
# To Export Fixtures , use this command :
# bench export-fixtures
# --------
# To export fixtures, use this command :
# bench export-fixtures

fixtures = [
    {"doctype": "DocType", "filters": {"custom": 1}},
    "Custom Field",
    "Custom Script",
    "Property Setter",
    "Letter Head",
    {"doctype": "Print Format", "filters": {"standard": "No"}},
    {"doctype": "Report", "filters": {"is_standard": "No"}},
    {
        "doctype": "Email Template",
        "filters": {"name": "Attendance Change Approval Notification"},
    },
]
