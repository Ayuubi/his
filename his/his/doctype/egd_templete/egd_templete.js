// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('EGD Templete', {
	template:function(frm){
		frm.set_value("template_code", frm.doc.template)
	}
});
