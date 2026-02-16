// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('General Surgery', {
	refresh: function(frm) {
		frm.set_query('drug_code', 'drug_prescription', function() {
			return {
				filters: {
					is_stock_item: 1
				}
			};
		});
        if(!frm.is_new()){
            frm.add_custom_button('Today ', () => {
                consoleerp_hi(frm.doc.patient , frm.doc.patient_name , true)
              }, 'History');
              frm.add_custom_button('History', () => {
                consoleerp_hi(frm.doc.patient , frm.doc.patient_name )
              }, 'History');
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
                    method: "his.his.doctype.general_surgery.general_surgery.refer", //dotted path to server method
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
                                    method: 'his.his.doctype.general_surgery.general_surgery.transfer', //dotted path to server method
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
               });
		}
	},
	select_lab_tests: function(frm){
        select_lab_tests(frm)
    }
,
	
	patient: function(frm) {
        
        let me = this
		if (frm.doc.patient) {
			frm.trigger('toggle_payment_fields');
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Patient',
					name: frm.doc.patient
				},
				callback: function(data) {
                    // alert(data.message.dob)
                    // console.log(data)
					let age = null;
					if (data.message.dob) {
						age = calculate_age(data.message.dob);
                       
					}
					frappe.model.set_value(frm.doctype, frm.docname, 'age', age);
					}


});
}
}
});
	let calculate_age = function(birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years =  age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};
