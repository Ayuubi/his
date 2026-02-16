// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Discharge Summery', {
	refresh: function(frm) {
        frm.set_query('drug_code', 'discharge_drug_prescription', function() {
            return {
                // query: "his.api.dp_drug_pr_link_query.my_custom_query",
                filters: {
                    is_stock_item: 1
                }
                
            };
        })

	}
});

frappe.ui.form.on('Drug Prescription', {
	refresh(frm) {

		// your code here
       
	}
})