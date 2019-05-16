# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "MIS HRIS",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("MIS HRIS")
		},
		{
			"module_name": "HR Add On",
			"color": "#2ecc71",
			"icon": "octicon octicon-organization",
			"label": _("Human Resources Add On"),
			"type": "module",
			"hidden": 1
		}
	]
