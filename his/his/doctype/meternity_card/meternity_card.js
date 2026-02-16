// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Meternity Card', {
	refresh: function(frm) {
		if(!frm.is_new()){
			var btn1 = frm.add_custom_button('Orders', () => {
				frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.practitioner })
		
			})
			btn1.addClass('btn-danger');

			var btn2 = frm.add_custom_button('POST Delivery', () => {
				frappe.new_doc("Post Delivery", {"patient": frm.doc.patient, "practitioner": frm.doc.practitioner })
		
			})
			btn2.addClass('btn-danger');

			
		}
	}
});
