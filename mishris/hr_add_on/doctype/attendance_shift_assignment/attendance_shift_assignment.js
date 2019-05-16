// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Shift Assignment', {
	setup: function(frm){
		frm.set_query('attendance_shift', function(){
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1
				}
			}
		});
	},
	refresh: function(frm) {

	}
});
