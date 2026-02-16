// Copyright (c) 2022, Rasiin and contributors
// For license information, please see license.txt

frappe.ui.form.on('PATIENT HANDOVER', {
	refresh: function(frm) {
		 frm.set_query('patient', () => {
    return {
        filters: {
            status: 'Admitted'
        }
    }
})


	},
	    patient: function(frm) {


		if (frm.doc.patient) {
			// frm.trigger('toggle_payment_fields');
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Inpatient Record',
					name: frm.doc.patient
				},
				callback: function(data) {
                    // alert(data.message.dob)
                    // console.log(data)
					console.log(data.message)
					frm.set_value("status",data.message.status);
					frm.set_value("patient_name",data.message.patient_name);
					frm.set_value("admitted_date",data.message.admitted_datetime);
					frm.set_value("location",data.message.admission_service_unit_type);
					frm.set_value("gender",data.message.gender);
					// frappe.model.set_value(frm.doctype, frm.docname, 'age', age);
                    // alert(data.message.is_insurance)

				}
			});
		}
	}
});
