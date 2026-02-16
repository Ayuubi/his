// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Materials Handover', {
	refresh: function(frm) {
		if (!frm.is_new() && frm.to_nurse == '') {
			var refurn_btn=  frm.add_custom_button(__("Accept Material"), function(){
				  
				frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Accept?`,
		 () => {
			 // action to perform if Yes is selected
						 frappe.call({
							method: "his.his.doctype.materials_handover.materials_handover.materials_handover",
							args: {
								docname: frm.doc.name,
							},
						 callback: function(r) {
							 
					 //frappe.msgprint(r)
					 console.log(r)
					 frappe.utils.play_sound("submit")
		
					 frappe.show_alert({
						 message:__('Materials Accepted Succesfully'),
						 indicator:'green',
						 
					 }, 5);}});},)});
			// ---------------------------------------------------------------------------------
			refurn_btn.addClass('btn-success');
		} 

	}
});
