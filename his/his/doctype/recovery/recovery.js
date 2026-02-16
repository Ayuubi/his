// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Recovery', {
	refresh(frm) {
		frm.disable_save();
		var btn3 = frm.add_custom_button('Vital Sign', () => {
			frappe.new_doc("Vital Signs", { "patient": frm.doc.patient })
	
		})
		btn3.addClass('btn-primary');
		var btn = frm.add_custom_button('Discharge', () => {
				frappe.new_doc("Discharge Summery", { "patient": frm.doc.patient, "ref_practitioner": frm.doc.consultant, "doctor_plan": frm.doc.name })
			
			})
			btn.addClass('btn-danger');
	
		var btn2 = frm.add_custom_button('Medication', () => {
			frappe.new_doc("Inpatient Medication", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
	
		})
		var btn1 = frm.add_custom_button('Requests', () => {
				frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.consultant, "source_order": "IPD" })
		
			})
		btn2.addClass('btn-danger');
	    // var transfer_btn=  frm.add_custom_button(__("Transfer To IPD"), function(){
		// 			frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Transfer <strong>${frm.doc.patient_name}</strong> to IPD?`,
		// 			() => {
		// 				frappe.utils.play_sound("submit")
		// 						frappe.show_alert({
		// 							message:__('Patient Transfered Succesfully'),
		// 							indicator:'green',
		// 						}, 5);
		// 						frappe.db.get_value("Patient",frm.doc.patient,"inpatient_status").then(
		// 							res => {
		// 								if(res.message.inpatient_status == "Admitted"){
		// 									frappe.db.set_value("Inpatient Record",frm.doc.inpatient_record,"inpatient_status","Admitted")
		// 								}
		// 								frm.savesubmit()
		// 							}
									
		// 							)
								
								
		// 						// frm.savesubmit()
		// 				// action to perform if Yes is selected
		// 				// frappe.call({
		// 				// 	method: 'his.his.doctype.recovery.recovery.transfer',
		// 				// 	args: {
		// 				// 		'name':frm.doc.name,
		// 				// 		'patient':frm.doc.patient,
		// 				// 		'sex':frm.doc.patient_sex,
		// 				// 		'service_unit':frm.doc.service_unit,
		// 				// 		'record':frm.doc.inpatient_record,
		// 				// 		'practitioner':frm.doc.practitioner,
		// 				// 		'status':frm.doc.status,
		// 				// 	},
		// 				// 	callback: function(r) {
		// 				// 		//frappe.msgprint(r)
		// 				// 		console.log(r)
		// 						// frappe.utils.play_sound("submit")
		// 						// frappe.show_alert({
		// 						// 	message:__('Patient Transfered Succesfully'),
		// 						// 	indicator:'green',
		// 						// }, 5);
		// 						// // frm.savesubmit()
		// 				// 	}
		// 				// });
		// 				},)
		// 			});
		// 			transfer_btn.addClass('btn-success');
					// var decharge=  frm.add_custom_button(__("Discharge Order"), function(){
					// frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Discharge <strong>${frm.doc.patient_name}</strong> to Recovery?`,
					// () => {
					// 	// action to perform if Yes is selected
					// 	frappe.call({
					// 		method: 'his.his.doctype.recovery.recovery.discharge',
					// 		args: {
					// 			'name':frm.doc.name,
					// 			'patient':frm.doc.patient,
					// 			'sex':frm.doc.patient_sex,
					// 			'service_unit':frm.doc.service_unit,
					// 			'record':frm.doc.inpatient_record,
					// 			'practitioner':frm.doc.practitioner,
					// 			'status':frm.doc.status,
					// 		},
					// 		callback: function(r) {
					// 			//frappe.msgprint(r)
					// 			console.log(r)
					// 			frappe.utils.play_sound("submit")
					// 			frappe.show_alert({
					// 				message:__('Patient Discharged Succesfully'),
					// 				indicator:'green',
					// 			}, 5);
					// 			// frm.savesubmit()					
					// 				}
					// 	});
					// 	},)
					// });
					// transfer_btn.addClass('btn-success');

			


			
	}


	
})
