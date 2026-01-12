frappe.ui.form.on('Anesthesia', {
	refresh(frm) {
		if (!frm.is_new()) {
			var btn1 = frm.add_custom_button('Requests', () => {
				frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.consultant, "source_order": "IPD" })
		
			})
		}
	}
});
