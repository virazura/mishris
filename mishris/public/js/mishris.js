frappe.ui.on.form('Payroll Entry', function(frm){
    refresh: function(frm) {
        frm.add_custom_button(__('Print Salary Slips'), function(){
            frappe.msgprint('Test');
        }, __("Utilities"));
    }
});
