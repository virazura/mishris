// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Summary Report', {
    refresh: function (frm) {

    },
    download_report: function (frm) {
        window.location.href = repl(frappe.request.url +
            '?cmd=%(cmd)s&start_date=%(start_date)s&end_date=%(end_date)s', {
                cmd: "mishris.hr_add_on.doctype.payroll_summary_report.payroll_summary_report.download_report",
                start_date: frm.doc.start_date,
                end_date: frm.doc.end_date,
            });
    }
});
