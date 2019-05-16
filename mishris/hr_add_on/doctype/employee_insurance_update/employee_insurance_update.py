# -*- coding: utf-8 -*-
# Copyright (c) 2019, MIS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import throw, _

class EmployeeInsuranceUpdate(Document):

    def validate(self):
        self.validate_insurance()

    def on_submit(self):
        self.insert_to_insurance_list()
    
    def insert_to_insurance_list(self):
        emp = frappe.get_doc('Employee', self.employee)
        emp.insurance_list = []
        
        # insert to employee insurance
        for ins in self.insurance_list:
            emp.append('insurance_list',{
                'insurance': ins.insurance,
                'insurance_name': ins.insurance_name,
                'company': ins.company,
                'insurance_number': ins.insurance_number,
                'is_bpjs': ins.is_bpjs,
                'policy': ins.policy,
                'is_default': ins.is_default})

            if(ins.is_default) and (ins.is_bpjs):
                emp.default_bpjs = ('{0} - {1}').format(ins.insurance, ins.policy)
                emp.default_bpjs_number = ins.insurance_number
            elif(ins.is_default) and (not ins.is_bpjs):
                emp.default_insurance = ('{0} - {1}').format(ins.insurance, ins.policy)
                emp.default_insurance_number = ins.insurance_number
            emp.save()

    def validate_insurance(self):
            totalbpjs = 0
            totalnonbpjs = 0
            for emp_ins in self.insurance_list:
                if (emp_ins.is_bpjs) and (emp_ins.is_default):
                    totalbpjs += 1
                elif (not emp_ins.is_bpjs) and (emp_ins.is_default):
                    totalnonbpjs += 1

                if (totalbpjs > 1) or (totalnonbpjs > 1):
                    throw(
                        _("You only can choose one in each type of insurance"))