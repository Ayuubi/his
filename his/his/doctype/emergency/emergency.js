// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Emergency', {
    select_imaging: function(frm){
        // alert("ok")
        select_imaging(frm)
    },
	refresh: function(frm) {

		if(!frm.is_new()){
            frm.add_custom_button('Today ', () => {
                consoleerp_hi(frm.doc.patient , frm.doc.patient_name , true)
              }, 'History');
              frm.add_custom_button('History', () => {
                consoleerp_hi(frm.doc.patient , frm.doc.patient_name )
              }, 'History');

              frm.add_custom_button('Transfer To OT', () => {
         
                let d = new frappe.ui.Dialog({
                    title: 'Select Procedure Name',
                    fields: [
                        {
                            label: 'Procedure',
                            fieldname: 'pro',
                            fieldtype: 'Link',
                            options: 'Clinical Procedure Template',
                            reqd : 1
                          
                        }
                     
                    ],
                    primary_action_label: 'Submit',
                    primary_action(values) {
                          let procedure = d.get_value("pro")
                        //   alert(procedure)
                     frappe.call({
                            method: "his.his.doctype.emergency.emergency.make_ot_schedule", //dotted path to server method
                            args: {
                                "docname": frm.doc.name,
                                "procedure" : procedure
                            },
                            callback: function(r) {
                                
                            frappe.utils.play_sound("submit")

                                frappe.show_alert({
                            message:__('You have Succesfully Transfared OT '),
                            indicator:'green',
                            
                        }, 5);
                        // cur_frm.print_doc()
                            }
                     });
                        
                     d.hide();
                    }
                    
                });
                
                d.show();

	
              }),
			frm.add_custom_button('Transfer To OPD', () => {
	     		    
	     		    
	     		    
	let d = new frappe.ui.Dialog({
    title: 'Enter details',
    fields: [
        {
            label: 'Practitioner',
            fieldname: 'practitioner',
            fieldtype: 'Link',
            options: 'Healthcare Practitioner',
            // reqd : 1,
            depends_on:  "eval: doc.out_side != 1",
        },
        {
            label: 'Out Side',
            fieldname: 'out_side',
            fieldtype: 'Check',
        },
        {
            fieldname: "to",
            fieldtype: "Data",
            label: "To",
            depends_on: "eval: doc.out_side",
        },
        {
            fieldname: "rtype",
            fieldtype: "Data",
            label: "Type",
            depends_on: "eval: doc.out_side",
        },
        {
            fieldname: "request",
            fieldtype: "Small Text",
            label: "Request",
            depends_on: "eval: doc.out_side",
        },
     
    ],
    primary_action_label: 'Submit',
    primary_action(values) {
          let practitioner = d.get_value("practitioner")
          let to = d.get_value("to")
          let rtype = d.get_value("rtype")
          let request = d.get_value("request")
          let out_side = d.get_value("out_side")
	if(! out_side){
	
            frappe.call({
                    method: "his.api.refer.refer", //dotted path to server method
                    args: {
                        "patient" : frm.doc.patient,
                        "practitioner" : practitioner,
                        "name": frm.doc.name,
                        "referring_practitioner": frm.doc.practitioner,
                    },
                    callback: function(r) {
                        // code snippet
                        // console.log(r)
                    // frm.set_value("status" , "Refered")
                     frappe.utils.play_sound("submit")

                        frappe.show_alert({
                    message:__('You have Refered Patient Succesfully'),
                    indicator:'green',
                    
                }, 5);
                // cur_frm.print_doc()
                    }
});
        d.hide();
    }
//     else{
    
//             frappe.call({
//                     method: "rasiin.api.refer.refer_out_side", //dotted path to server method
//                     args: {
//                         "docname" : frm.doc.patient,
//                         "practitioner" : frm.doc.practitioner,
//                         "to": to,
//                         "rtype": rtype,
//                         "request": request,
//                         "patient": frm.doc.patient,
//                     },
//                     callback: function(r) {
//                         // code snippet
//                         // console.log(r)
//                     // frm.set_value("status" , "Refered")
//                      frappe.utils.play_sound("submit")

//                         frappe.show_alert({
//                     message:__('You have Refered Patient Succesfully'),
//                     indicator:'green'
//                 }, 5);
//                     }
// });
//         d.hide();
//     }
    }
	
});

d.show();
	     		    
	     		    
	     		    
	     		    
	     		    
	     		    
	     		
               
            })
			// ---------------------------------------------------------------------------------------------------------------------------
			frm.add_custom_button(__("Transfer To IPD"), function(){
                let d = new frappe.ui.Dialog({
                    title: 'Enter details',
                    fields: [
                        {
                            label: 'Diagnose',
                            fieldname: 'diagnose',
                            fieldtype: 'Data',
                            reqd : 1,
                        },
                        
                     
                    ],
                    primary_action_label: 'Submit',
                    primary_action(values) {
                          let diagnose = d.get_value("diagnose")
                         
                    
                    
                            frappe.call({
                                    method: "his.his.doctype.emergency.emergency.transfer", //dotted path to server method
                                    args: {
                                        "diagnose" : diagnose,
                                        'patient':frm.doc.patient,
                                        'name': frm.doc.name,
                                        'practitioner':frm.doc.practitioner,
                                        
                                    },
                                    callback: function(r) {
                                       
                                     frappe.utils.play_sound("submit")
                
                                        frappe.show_alert({
                                    message:__('You have Transfered Patient Succesfully'),
                                    indicator:'green',
                                    
                                }, 5);
                               
                                    }
                });
                        d.hide();
                    }
                
                    
                    
                });
                d.show();
					// frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Transfer <strong>${frm.doc.patient_name}</strong> to IPD?`,
					// () => {
					// 	// action to perform if Yes is selected
					// 	frappe.call({
					// 		method: 'his.his.doctype.emergency.emergency.transfer',
					// 		args: {
								
					// 			'patient':frm.doc.patient,
					// 			'name': frm.doc.name,
					// 			'practitioner':frm.doc.practitioner,
								
					// 		},
					// 		callback: function(r) {
					// 			//frappe.msgprint(r)
					// 			frappe.utils.play_sound("submit")
					// 			frappe.show_alert({
					// 				message:__('Patient Transfered Succesfully'),
					// 				indicator:'green',
					// 			}, 5);
					// 		}
					// 	});
					// 	},)
					});
		}
	},
    after_save: function(frm){
        window.location.reload();
    },
    select_lab_tests: function(frm){
        select_lab_tests(frm)
    }
	
});
