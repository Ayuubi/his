/*
(c) ESS 2015-16
*/
frappe.listview_settings['OT Schedule'] = {
	filters: [["status", "=", "Not Scheduled"]],
	get_indicator: function(doc) {
		var colors = {
			"Not Scheduled": "orange",
			"Scheduled": "yellow",
			"Closed": "green",
			"Cancelled": "red",
			"Expired": "grey"
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	}
};
