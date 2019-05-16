# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class KartuKeluarga(Document):
	
	def on_update(self):
		self.insert_kk()

	def insert_kk(self):
		doc = frappe.get_doc("Employee",self.employee)
		if (not doc.kartu_keluarga) or (doc.kartu_keluarga != self.no) :
			doc.kartu_keluarga = self.no
			doc.save() 