frappe.ui.form.on('Inpatient Record', {

	refresh: function(frm) {
		// alert("ok in public")
		frm.remove_custom_button('Admit');
        frm.remove_custom_button('Discharge');
        if(frm.doc.status == "Discharge Scheduled"){
            var refurn_btn=  frm.add_custom_button(__("Discharge"), function(){
                if(frm.doc.clearance_status != "Cleared"){
                    // with options
                frappe.msgprint({
                    title: __('Uncleared Inpatient'),
                    indicator: 'red',
                    message: __(`<strong>${frm.doc.patient_name} </strong> , is Uncleared Please Ask Cashiers to Clear`)
                });

                }
                else{
					frappe.call({
						method: "his.api.inpatient_record.check_out_inpatient", //dotted path to server method
						args: {
							'inpatient_record' : frm.doc.name
						},
						callback: function(r) {
							// code snippet
							// console.log(r)
						// frm.set_value("status" , "Refered")
						
						frm.reload_doc();
						
						frappe.utils.play_sound("submit")

						frappe.show_alert({
						message:__('You have Discharged Patient Succesfully'),
						indicator:'green',
						
					}, 5);
						}
					});
                    // frappe.call({
                    //     method: 'his.api.inpatient_record.check_out_inpatient',
					// 	args: {
					// 		inpatient_record: frm.doc.name,
							
					// 	},
                    //     callback: function(data) {
                    //         if (!data.exc) {
                    //             frm.reload_doc();
                    //         }
                    //     },
                    //     freeze: true,
                    //     freeze_message: __('Processing Inpatient Discharge')
                    // });
                }
            })
        }      

		if (!frm.doc.__islocal) {
			if (frm.doc.status == 'Admitted' && !frm.doc.accepted_or_rejected) {
				var refurn_btn=  frm.add_custom_button(__("Accept"), function(){
                      
					frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Accept?`,
			 () => {
				 // action to perform if Yes is selected
							 frappe.call({
								method: "his.api.inpatient_record.inpatient_record",
								args: {
									docname: frm.doc.name,
									admitted_status:'Accepted'
								},
							 callback: function(r) {
								 
						 //frappe.msgprint(r)
						 console.log(r)
						 frappe.utils.play_sound("submit")
			
						 frappe.show_alert({
							 message:__('Patient Accepted Succesfully'),
							 indicator:'green',
							 
						 }, 5);}});},)});
				// ---------------------------------------------------------------------------------
				refurn_btn.addClass('btn-success');
				
				


				var reject_btn=  frm.add_custom_button(__("Reject"), function(){
					let d = new frappe.ui.Dialog({
					    title: 'Enter the reason',
					    fields: [
					        {
					            label: 'Reason',
					            fieldname: 'reason',
					            fieldtype: 'Small Text',
					            reqd:1
					            // frm.toggle_reqd("reason", true)
					        },
					  
					    ],
					    primary_action_label: 'Submit',
					    primary_action(values) {
								frappe.call({
									method: "his.api.inpatient_record.inpatient_record",
									args: {
										reason: values.reason,
										docname: frm.doc.name,
										admitted_status:'Rejected',
										
									},
								 callback: function(r) {
									 
							 //frappe.msgprint(r)
							 console.log(r)
							 frappe.utils.play_sound("submit")
				
							 frappe.show_alert({
								 message:__('Patient Rejected Succesfully'),
								 indicator:'red',
								 
							 }, 5);}});
					        d.hide();
					    }
					});

					d.show();

					});
				
				// ---------------------------------------------------------------------------------
				reject_btn.addClass('btn-primary');
			} 
            if(frm.doc.status == "Admission Scheduled"){
				var read_ot=  frm.add_custom_button(__("Ready To Procedure"), function(){
                      
					frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to make OT Schedule?`,
			 () => {
				 // action to perform if Yes is selected
							 frappe.call({
								method: "his.api.ot_prepation.make_ot_schedule",
								args: {
									docname: frm.doc.name,
									
								},
							 callback: function(r) {
								 
						 //frappe.msgprint(r)
						 console.log(r)
						 frappe.utils.play_sound("submit")
			
						 frappe.show_alert({
							 message:__('Patient Accepted Succesfully'),
							 indicator:'green',
							 
						 }, 5);}});},)});
				// ---------------------------------------------------------------------------------
				read_ot.addClass('btn-success');
			frm.add_custom_button('Admit IPD', () => {

	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			 {
				label: 'Type',
				fieldname: 'type',
				fieldtype: 'Link',
				options :'Inpatient Type'
			},
			{
				label: 'Room',
				fieldname: 'room',
				fieldtype: 'Link',
				options :'Healthcare Service Unit Type'
			}
			   
	
		],
		primary_action_label: 'Submit',
		primary_action(values) {
			// alert("ok")
				// console.log(values.room)
			   frappe.route_options = {'room': values.room , "type" : values.type  , "inp_doc" : frm.doc.name , "inp_dt" : frm.doc  , "patient" : frm.doc.patient };
				frappe.set_route('room');
			d.hide();
		}
	});
		d.fields_dict['room'].get_query = function(){
		return {
			filters: {
				'inpatient_occupancy': 1,
				'Type':"IPD"
			}
		};
	};
	
	d.show();
	   
	})
}
		}

	}
});
