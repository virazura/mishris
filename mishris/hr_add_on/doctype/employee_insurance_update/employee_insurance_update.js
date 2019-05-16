// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Insurance Update', {
    validate: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var totalbpjs = 0;
        var totalnonbpjs = 0;
        frm.doc.insurance_list.forEach(function (row) {
            if (row.is_bpjs && row.is_default) {
                totalbpjs++;
                if (totalbpjs > 1) {
                    frappe.throw('You only can choose one in each type of insurance');
                    frappe.validated = false;
                }
            }
            if (!row.is_bpjs && row.is_default) {
                totalnonbpjs++;
                if (totalnonbpjs > 1) {
                    frappe.throw('You can only choose one in each type of insurance');
                    frappe.validated = false;
                }
            }
        });
    },

    employee: function (frm) {
        frm.doc.insurance_list = []
        if (frm.doc.employee) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    name: frm.doc.employee,
                    doctype: "Employee"
                },
                callback: function (r) {
                    if (r.message) {
                        for (var row in r.message.insurance_list) {
                            var child = frm.add_child("insurance_list");
                            frappe.model.set_value(child.doctype, child.name, "insurance",
                                r.message.insurance_list[row].insurance);
                            frappe.model.set_value(child.doctype, child.name, "insurance_name",
                                r.message.insurance_list[row].insurance_name);
                            frappe.model.set_value(child.doctype, child.name, "insurance_number",
                                r.message.insurance_list[row].insurance_number);
                            frappe.model.set_value(child.doctype, child.name, "is_bpjs",
                                r.message.insurance_list[row].is_bpjs);
                            frappe.model.set_value(child.doctype, child.name, "policy",
                                r.message.insurance_list[row].policy);
                            frappe.model.set_value(child.doctype, child.name, "is_default",
                                r.message.insurance_list[row].is_default);
                        }
                    }
                    frm.refresh_field('insurance_list')
                }
            })
        }
    },

    onload: function (frm, cdt, cdn) {
        var df = frappe.meta.get_docfield('Employee Insurance', "insurance", frm.doc.name);
        var dg = frappe.meta.get_docfield('Employee Insurance', "insurance_number", frm.doc.name);
        var dh = frappe.meta.get_docfield('Employee Insurance', "is_default", frm.doc.name);
        df.read_only = 0;
        dg.read_only = 0;
        dh.read_only = 0;
        frm.refresh_field('insurance_list')
    }
});


frappe.ui.form.on('Employee Insurance', {
    insurance_list_remove: function (frm) {
        frappe.model.with_doc('Employee Insurance Update', frm.doc.employee, function () {
            frm.refresh_field('employee');
        });
    }
});

