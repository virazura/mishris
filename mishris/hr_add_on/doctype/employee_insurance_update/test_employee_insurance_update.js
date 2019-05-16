QUnit.module('employee_insurance_update');
QUnit.test("test: Employee Insurance Update", function(assert) {
	let done = assert.async();
	assert.expect(9);
	frappe.run_serially([
		() => 
			 frappe.tests.make('Employee Insurance Update', [
				{employee: 'HR-EMP-00010'},
				{insurance_list: [
					[
						{'insurance': 'Reliance'},
                        {'insurance_number': '12345'},
                        {'is_default': true}
					],
					[
						{'insurance': 'Axa'},
                        {'insurance_number': '123455'},
                        {'is_default': true}
					],
					[
						{'insurance': 'Allianz'},
                        {'insurance_number': '123456'},
                        {'is_default': true}
					],

				]}
            ]),
		() => {
			assert.ok(cur_frm.doc.insurance_list[0].insurance=='Reliance');
			assert.ok(cur_frm.doc.insurance_list[0].insurance_number=='12345');
			assert.ok(cur_frm.doc.insurance_list[0].is_default==true);
			assert.ok(cur_frm.doc.insurance_list[1].insurance=='Axa');
			assert.ok(cur_frm.doc.insurance_list[1].insurance_number=='123455');
			assert.ok(cur_frm.doc.insurance_list[1].is_default==true);
			assert.ok(cur_frm.doc.insurance_list[2].insurance=='Allianz');
			assert.ok(cur_frm.doc.insurance_list[2].insurance_number=='123456');
			assert.ok(cur_frm.doc.insurance_list[2].is_default==true);
		},
		() => done()
	]);
});