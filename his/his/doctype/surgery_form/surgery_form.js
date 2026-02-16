// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Surgery Form', {
	refresh: function(frm) {
		$('.indicator-pill').show()
		$('.standard-actions').show()
		frm.enable_save();

	}
});
