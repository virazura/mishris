// Copyright (c) 2019, MIS and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'company', 'company');
frappe.ui.form.on('Employee Tax Income', {
	setup: function(frm) {
		$.each(["earnings", "deductions"], function(i, table_fieldname) {
			frm.get_field(table_fieldname).grid.editable_fields = [
				{fieldname: 'salary_component', columns: 6},
				{fieldname: 'amount', columns: 4}
			];
		})
		frm.set_query("salary_component", "earnings", function() {
			return {
				filters: {
					type: "earning"
				}
			}
		})
		frm.set_query("salary_component", "deductions", function() {
			return {
				filters: {
					type: "deduction"
				}
			}
		})
	},
	refresh: function(frm) {
		frm.trigger("toggle_fields")
		frm.trigger("toggle_reqd_fields")
		var salary_detail_fields = ["formula", "abbr", "statistical_component", "is_tax_applicable",
			"is_flexible_benefit", "variable_based_on_taxable_salary", "is_additional_component"]
		cur_frm.fields_dict['earnings'].grid.set_column_disp(salary_detail_fields,false);
		cur_frm.fields_dict['deductions'].grid.set_column_disp(salary_detail_fields,false);
	},
});
frappe.ui.form.on('Salary Detail', {
	earnings_remove: function(frm, dt, dn) {
		calculate_all(frm.doc, dt, dn);
	},
	deductions_remove: function(frm, dt, dn) {
		calculate_all(frm.doc, dt, dn);
	}
});
var calculate_all = function(doc, dt, dn) {
	calculate_earning_total(doc, dt, dn);
	calculate_ded_total(doc, dt, dn);
	calculate_net_pay(doc, dt, dn);
};


// Get leave details
//---------------------------------------------------------------------
var get_emp_and_leave_details = function(doc, dt, dn) {
	return frappe.call({
		method: 'get_emp_and_leave_details',
		doc: locals[dt][dn],
		callback: function(r, rt) {
			cur_frm.refresh();
			calculate_all(doc, dt, dn);
		}
	});
}

cur_frm.cscript.employee = function(doc,dt,dn){
	get_emp_and_leave_details(doc, dt, dn);
}

cur_frm.cscript.salary_slip = function(doc,dt,dn){
	get_emp_and_leave_details(doc, dt, dn);
}
// Calculate earning total
// ------------------------------------------------------------------------
var calculate_earning_total = function(doc, dt, dn, reset_amount) {

	var tbl = doc.earnings || [];
	var total_earn = 0;
	for(var i = 0; i < tbl.length; i++){
		if(cint(tbl[i].depends_on_lwp) == 1) {
			tbl[i].amount =  Math.round(tbl[i].default_amount)*(flt(doc.payment_days) /
				cint(doc.total_working_days)*100)/100;
		} else if(reset_amount && tbl[i].default_amount) {
			tbl[i].amount = tbl[i].default_amount;
		}
		if(!tbl[i].do_not_include_in_total) {
			total_earn += flt(tbl[i].amount);
		}
	}
	doc.gross_pay = total_earn;
	refresh_many(['earnings', 'amount','gross_pay']);

}

// Calculate deduction total
// ------------------------------------------------------------------------
var calculate_ded_total = function(doc, dt, dn, reset_amount) {
	var tbl = doc.deductions || [];
	var total_ded = 0;
	for(var i = 0; i < tbl.length; i++){
		if(cint(tbl[i].depends_on_lwp) == 1) {
			tbl[i].amount = Math.round(tbl[i].default_amount)*(flt(doc.payment_days)/cint(doc.total_working_days)*100)/100;
		} else if(reset_amount && tbl[i].default_amount) {
			tbl[i].amount = tbl[i].default_amount;
		}
		if(!tbl[i].do_not_include_in_total) {
			total_ded += flt(tbl[i].amount);
		}
	}
	doc.total_deduction = total_ded;
	refresh_many(['deductions', 'total_deduction']);
}

// Calculate net payable amount
// ------------------------------------------------------------------------
var calculate_net_pay = function(doc, dt, dn) {
	doc.net_pay = flt(doc.gross_pay) - flt(doc.total_deduction);
	doc.rounded_total = Math.round(doc.net_pay);
	refresh_many(['net_pay', 'rounded_total']);
}

// validate
// ------------------------------------------------------------------------
cur_frm.cscript.validate = function(doc, dt, dn) {
	calculate_all(doc, dt, dn);
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}
}

// calculate total working hours, earnings based on hourly wages and totals
// ------------------------------------------------------------------------
var total_work_hours = function(frm, dt, dn) {
	frm.set_value('total_working_hours', 0);

	$.each(frm.doc["timesheets"] || [], function(i, timesheet) {
		frm.doc.total_working_hours += timesheet.working_hours;
	});
	frm.refresh_field('total_working_hours');

	var wages_amount = frm.doc.total_working_hours * frm.doc.hour_rate;

	frappe.db.get_value('Salary Structure', {'name': frm.doc.salary_structure}, 'salary_component', (r) => {
		frm.set_value('gross_pay', 0);

		$.each(frm.doc["earnings"], function(i, earning) {
			if (earning.salary_component == r.salary_component) {
				earning.amount = wages_amount;
				frm.refresh_fields('earnings');
			}
			frm.doc.gross_pay += earning.amount;
		});

		frm.refresh_field('gross_pay');
		calculate_net_pay(frm.doc, dt, dn);
	});
}
