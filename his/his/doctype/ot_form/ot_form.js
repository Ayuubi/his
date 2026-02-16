// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('OT Form', {
	refresh: function(frm) {
		refresh_field('drug');
		refresh_field('other_service');
		frm.set_query('item', 'drug', function() {
			return {
				filters: {
					// item_group: ['not in', ['Cunto', 'Cabitaan','Shaah/Coffee']]
					for_canteen: 0
				}
			};
		});

		frm.set_query('item', 'other_service', function() {
			return {
				filters: {
					// item_group: ['not in', ['Cunto', 'Cabitaan','Shaah/Coffee']]
					for_canteen: 0
				}
			};
		});
	}
});
