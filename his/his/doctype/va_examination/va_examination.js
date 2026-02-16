frappe.ui.form.on('VA Examination', {
	refresh(frm) {
	  if (!frm.is_new() && frm.doc.docstatus !== 2) {
		frm.add_custom_button(__('Create EyeGlass Prescription'), async () => {
		  if (frm.__creating_presc) return;   // anti-double-click
		  frm.__creating_presc = true;
  
		  frappe.call({
			method: 'his.his.doctype.va_examination.va_examination.create_eyeglass_prescription',
			args: { va_exam_name: frm.doc.name },
			freeze: true,
			freeze_message: __('Creating EyeGlass Prescription...'),
			callback: (r) => {
			  const d = r.message;
			  if (d?.status === 'exists') {
				frappe.show_alert({ message: __('Prescription already exists: {0}', [d.name]), indicator: 'orange' }, 7);
			  } else if (d?.status === 'created') {
				frappe.show_alert({ message: __('Prescription created: {0}', [d.name]), indicator: 'green' }, 7);
			  } else {
				frappe.show_alert({ message: __('Could not create prescription'), indicator: 'red' }, 7);
			  }
			},
			always: () => { frm.__creating_presc = false; }
		  });
		}, __('Create'));
	  }
	}
  });
  