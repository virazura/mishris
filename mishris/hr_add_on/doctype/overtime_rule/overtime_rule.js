// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Rule', {
    setup: function(frm) {
        frm.set_query('bracket', 'overtime_rule_list', function(doc, cdt, cdn){
            return {
                filters: {
                    company: frm.doc.company
                }
            }
        });
    }
});
