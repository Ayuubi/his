// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt
frappe.provide('erpnext.queries');
frappe.ui.form.on('CT Scan', {
	// refresh: function(frm) {

	// }
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
})
	let calculate_age = function(birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years =  age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};
