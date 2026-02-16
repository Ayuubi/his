// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Other Service', {
	template: function(frm) {
		
			frm.set_value('template_code', frm.doc.template);
			// frm.set_value('item_code', frm.doc.template);
			frm.set_value('description', frm.doc.template);
	},
	// refresh : function(frm) {
	// 	// Restrict Special, Grouped type templates in Child Test Groups
	// 	frm.set_query('lab_test_template', 'item_groups', function() {
	// 		return {
	// 			filters: {
	// 				lab_test_template_type: ['in', ['Single','Compound']]
	// 			}
	// 		};
	// 	});
	// },
	medical_code: function(frm) {
		frm.set_query('medical_code', function() {
			return {
				filters: {
					medical_code_standard: frm.doc.medical_code_standard
				}
			};
		});
	}
});

cur_frm.cscript.custom_refresh = function(doc) {
	cur_frm.set_df_property('template_code', 'read_only', doc.__islocal ? 0 : 1);

	if (!doc.__islocal) {
		cur_frm.add_custom_button(__('Change Template Code'), function() {
			change_template_code(doc);
		});
	}
};

let change_template_code = function(doc) {
	let d = new frappe.ui.Dialog({
		title:__('Change Template Code'),
		fields:[
			{
				'fieldtype': 'Data',
				'label': 'Template Code',
				'fieldname': 'template_code',
				reqd: 1
			}
		],
		primary_action: function() {
			let values = d.get_values();
			if (values) {
				frappe.call({
					'method': 'erpnext.healthcare.doctype.lab_test_template.lab_test_template.change_test_code_from_template',
					'args': {template_code: values.template_code, doc: doc},
					callback: function (data) {
						frappe.set_route('Form', 'Other Service', data.message);
					}
				});
			}
			d.hide();
		},
		primary_action_label: __('Change Template Code')
	});
	d.show();

	d.set_values({
		'template_code': doc.template_code
	});
};

frappe.ui.form.on('Other Service', 'template', function(frm) {
	frm.doc.change_in_item = 1;
});

frappe.ui.form.on('Other Service', 'lab_test_rate', function(frm) {
	frm.doc.change_in_item = 1;
});

frappe.ui.form.on('Other Service', 'item_group', function(frm) {
	frm.doc.change_in_item = 1;
});

frappe.ui.form.on('Other Service', 'description', function(frm) {
	frm.doc.change_in_item = 1;
});

// frappe.ui.form.on('Lab Test Groups', 'template_or_new_line', function (frm, cdt, cdn) {
// 	let child = locals[cdt][cdn];
// 	if (child.template_or_new_line == 'Add New Line') {
// 		frappe.model.set_value(cdt, cdn, 'lab_test_template', '');
// 		frappe.model.set_value(cdt, cdn, 'description', '');
// 	}
// });
