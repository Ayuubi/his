// Copyright (c) 2022, Rasiin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Aneasthesia Sheet', {
	refresh(frm) {
	    if (!frm.is_new()) {
	    	 
			if (frm.doc.status == 'Admitted'){
				// var transfer_btn=  frm.add_custom_button(__("Transfer To Recovery"), function(){
				// 	frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Transfer <strong>${frm.doc.patient_name}</strong> to Recovery?`,
				// 	() => {
				// 		// action to perform if Yes is selected
				// 		frappe.call({
				// 			method: 'his.his.doctype.aneasthesia_sheet.aneasthesia_sheet.transfer',
				// 			args: {
				// 				service_unit:frm.doc.service_unit,
				// 				docname: frm.doc.name,
				// 				patient: frm.doc.patient,
				// 				clinical_procedure : frm.doc.clinical_procedure,
				// 				practitioner : frm.doc.operative_doctor
				// 			},
				// 			callback: function(r) {
				// 				//frappe.msgprint(r)
				// 				console.log(r)
				// 				frappe.utils.play_sound("submit")
				// 				frappe.show_alert({
				// 					message:__('Patient Transfered Succesfully'),
				// 					indicator:'green',
				// 				}, 5);
				// 			}
				// 		});
				// 		},)
				// 	});
				// 	transfer_btn.addClass('btn-success');
			}
			
				if (!frm.doc.service_unit){
					frm.add_custom_button('Admit', () => {
						let d = new frappe.ui.Dialog({
							 title: 'Admit Patient',
							 fields: [
								{
									fieldtype: 'Link', 
									label: 'Service Unit Type', 
									fieldname: 'service_unit_type',
									options: 'Healthcare Service Unit Type', 
									// default: frm.doc.admission_service_unit_type
									// reqd : 1,
								},
								{
									fieldtype: 'Link', 
									label: 'Service Unit', 
									fieldname: 'service_unit',
									options: 'Healthcare Service Unit',
									reqd: 1
								},
							// {
							//     fieldtype: 'Date', 
							//     label: 'Expected Discharge',
							//     fieldname: 'date',
							// 	default: frm.doc.date ? frappe.datetime.add_days(frappe.datetime.now_datetime(), frm.doc.date) : ''
							// }
		 
		],
							primary_action_label: 'Admit',
							primary_action(values) {
								let service_unit = d.get_value('service_unit');
									if (!service_unit && !check_in) {
										return;
									}
									frappe.call({
										doc: frm.doc,
										method: 'admit',
										args:{
											'service_unit': service_unit,
											// 'date': date
										},
										callback: function(data) {
											if (!data.exc) {
												frm.reload_doc();
											}
										},
										freeze: true,
										freeze_message: __('Processing Patient Admission')
									});
									frm.refresh_fields();
									d.hide();
								}});
							d.fields_dict['service_unit_type'].get_query = function() {
								return {
									filters: {
										'inpatient_occupancy': 1,
										'allow_appointments': 0,
										'type': 'OT'
									}
								};
							};
							d.fields_dict['service_unit'].get_query = function() {
								return {
									filters: {
										'is_group': 0,
										'company': frm.doc.company,
										'service_unit_type': d.get_value('service_unit_type'),
										'occupancy_status' : 'Vacant'
									}
								};
							};
	
							d.show();	
									
									})  
				}
			

						}

						}
})