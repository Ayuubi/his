// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('OT Prepartion', {
	refresh: function(frm) {
		frm.set_query('item_code', 'consumable_items', function () {
			return {
				filters: {
					is_stock_item: 1
				}
			};
		});
		if (frm.doc.docstatus == 1 && !frm.doc.aneasthesia){
			var Aneasthesia_btn=  frm.add_custom_button(__("Aneasthesia"), function(){
				frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Create Aneasthesia for <strong>${frm.doc.patient_name}</strong> ?`,
				() => {
					// action to perform if Yes is selected
					frappe.call({
						method: 'his.api.clinical_procedure.aneasthesia_sheet',
						args: {
							docname: frm.doc.ot_schedule,
							patient: frm.doc.patient,
							procedure_template: frm.doc.procedure_template,
							operative_doctor: frm.doc.practitioner
						},
						callback: function(r) {
							//frappe.msgprint(r)
							console.log(r)
							frappe.utils.play_sound("submit")
							frappe.show_alert({
								message:__('Aneasthesia Created '),
								indicator:'green',
							}, 5);
							frm.set_value('aneasthesia', 1)
							frm.save("Update")
							// frm.reload_doc()
							// alert(frm.doc.aneasthesia)
						}
					});
					},)
				});
				Aneasthesia_btn.addClass('btn-success');
		}
		frm.set_query('item_code', 'billible_items', function() {
			return {
				filters: {
					is_stock_item: 1
				}
			};
		});

		frm.set_query('drug_code', 'drug_prescription', function() {
			return {
				filters: {
					is_stock_item: 1
				}
			};
		});
	}
});
