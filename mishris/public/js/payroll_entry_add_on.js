frappe.ui.form.on('Payroll Entry', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
				if (frm.custom_buttons) frm.clear_custom_buttons();
				frm.events.add_export_account(frm);
		}
	},
	add_export_account: function(frm) {	
		if(frm.doc.salary_slips_submitted) {
			frm.add_custom_button(__("Export BCA"), function() {
				export_xls(frm, 'BCA');
			}).addClass("btn-primary");
			frm.add_custom_button(__("Export Other Bank"), function() {
				export_xls(frm, 'Other');
			}).addClass("btn-primary");
		}
	},
});

let export_xls = function (frm, bank) {
	var doc = frm.doc.name;
	var bank = bank
	window.location.href = repl(frappe.request.url +
            '?cmd=%(cmd)s&from_date=%(from_date)s&to_date=%(to_date)s', {
            cmd: "mishris.hr_add_on.payroll_entry_addon.export_bank_entry",
            payroll_entry: doc,
            bank: bank,
        });
};
