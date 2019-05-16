// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Change Request', {
    refresh: function(frm) {
        if(frm.doc.employee && frm.doc.attendance_date){
            frm.add_custom_button(__("Show Employee Attendance"), function () {
                frappe.set_route("List", "Attendance", {
                    employee: frm.doc.employee,
                    attendance_date: frm.doc.attendance_date
                });
            });
        }
    },
    setup: function(frm){
        frm.set_query("new_attendance", function () {
            return {
                filters: {
                    employee: frm.doc.employee,
                    attendance_date: frm.doc.attendance_date,
                    docstatus: 1
                }
            }
        });
        frm.set_query("attendance_approver", function(){
            return {
                query: "mishris.hr_add_on.doctype.attendance_department_approver.attendance_department_approver.get_attendance_approvers",
                filters: {
                    employee: frm.doc.employee,
                    doctype: frm.doc.doctype
                }
            };
        });
        frm.set_query("employee", erpnext.queries.employee);
    },
    employee: function(frm){
        frm.trigger("set_attendance_approver");
    },
    attendance_approver: function(frm){
        if(frm.doc.attendance_approver){
            frm.set_value("attendance_approver_name", frappe.user.full_name(frm.doc.attendance_approver));
        }
    },
    set_attendance_approver: function(frm){
        if(frm.doc.employee){
            frappe.call({
                method: "mishris.hr_add_on.doctype.attendance_change_request.attendance_change_request.get_attendance_approver",
                args: {
                    employee: frm.doc.employee
                },
                callback: function(r){
                    if(r && r.message){
                        frm.set_value('attendance_approver', r.message);
                        // frm.trigger('attendance_approver');
                    }
                }
            });
        }
    },
    before_submit: function (frm) {
        if (!frm.doc.new_attendance) {
            frappe.throw('New Attendance must be filled before submit');
        }
    }
});


