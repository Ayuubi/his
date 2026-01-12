// Copyright (c) 2022, Anfac and contributors
// For license information, please see license.txt

frappe.ui.form.on('Lab Result', {
	refresh: function(frm) {
	// 	frm.add_custom_button('Print', () => {
	
	// 		if(frm.doc.template == "CBC"){
	// 			window.open(`
	
	
	// 					${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=cbc&no_letterhead=0&letterhead=logo&settings=%7B%7D&_lang=en-US`);
				
				
	// 		}
	// 		else if(frm.doc.type == "Group"){

	// 			window.open(`


	// 			${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=Urine%20Report&no_letterhead=0&letterhead=logo&settings=%7B%7D&_lang=en-US

		
		
	// 			`);

				
	// 							}

	// 				else if(frm.doc.type == "Hormones"){

	// 					window.open(`
	
	
	// 					${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=hormone&no_letterhead=0&letterhead=logo&settings=%7B%7D&_lang=en-US
	
				
				
	// 					`);
						
						
	// 									}
	// 		else{
	// 		window.open(`
	// 		${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=lab%20result%20report&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US		`);
		
	// }
	// 	})

	frm.add_custom_button("Print", () => {
		window.open(`
			${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=Lab%20Result%20Print%20for%20All%20Tests&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`);	
		})
	}
});
