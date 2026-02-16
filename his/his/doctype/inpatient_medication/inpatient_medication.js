// Copyright (c) 2021, Rasiin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inpatient Medication', {
	refresh: function(frm) {

        frappe.call({
			method: "his.his.doctype.inpatient_medication.inpatient_medication.get_billed_items", //dotted path to server method
			args :{

				patient: frm.doc.patient
			},
			callback: function(r) {
				// code snippet
				console.log(r.message)

                frm.set_query('drug', 'treatment_sheet', function() {
                    return {
                        // query: "his.api.dp_drug_pr_link_query.my_custom_query",
                        filters: {
                           name: ['in', r.message]
                        }
                        
                    };
                })
				
			}
		});
		// frm.set_query('drug', 'treatment_sheet', function() {
        //     return {
        //         // query: "his.api.dp_drug_pr_link_query.my_custom_query",
        //         filters: {
        //             is_stock_item: 1
        //         }
                
        //     };
        // })

	}
});
