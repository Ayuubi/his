// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Packages', {
	
	package: function(frm){
		setTimeout(function(){
			// alert(frm.doc.doctor_number);
			if(frm.doc.package_amount && frm.doc.doctor_number){
		
			frm.set_value("total", frm.doc.package_amount+frm.doc.doctor_number)
		}
		
		
		}, 100);
	
	},
	after_save: function(frm){
		frm.set_df_property('patient',  'read_only',   1);
		frm.set_df_property('practitioner',  'read_only',   1);
		frm.set_df_property('package',  'read_only',   1);
		frm.set_df_property('date',  'read_only',   1);
		frm.set_df_property('paid_amount',  'read_only',   1);
	}
});
