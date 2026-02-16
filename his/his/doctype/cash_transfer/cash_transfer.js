// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Transfer', {
	refresh: function(frm) {
		if(frm.is_new()){
			frm.set_value("username",frappe.session.user)
			// alert(frappe.session.full_name)
		}
	}
});
