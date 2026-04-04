// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Customer Balance Statement"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer"
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group"
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "All\nCustomer Owes Us\nWe Owe Customer\nSettled",
			default: "All"
		},
		{
			fieldname: "only_with_activity",
			label: __("Only With Activity"),
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "only_non_zero_balance",
			label: __("Only Non Zero Balance"),
			fieldtype: "Check",
			default: 1
		}
	],

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		// Status coloring
		if (column.fieldname === "status") {
			if (data.status === "Customer Owes Us") {
				value = `<span style="color:#d9534f;font-weight:700;">${value}</span>`;
			} else if (data.status === "We Owe Customer") {
				value = `<span style="color:#28a745;font-weight:700;">${value}</span>`;
			} else if (data.status === "Settled") {
				value = `<span style="color:#5b9bd5;font-weight:700;">${value}</span>`;
			}
		}

		// Closing balance coloring
		if (column.fieldname === "closing_balance") {
			if (flt(data.closing_balance) > 0) {
				value = `<span style="color:#d9534f;font-weight:700;">${value}</span>`;
			} else if (flt(data.closing_balance) < 0) {
				value = `<span style="color:#28a745;font-weight:700;">${value}</span>`;
			} else {
				value = `<span style="color:#5b9bd5;font-weight:700;">${value}</span>`;
			}
		}

		// Today balance coloring
		if (column.fieldname === "today_balance") {
			if (flt(data.today_balance) > 0) {
				value = `<span style="color:#d9534f;font-weight:700;">${value}</span>`;
			} else if (flt(data.today_balance) < 0) {
				value = `<span style="color:#28a745;font-weight:700;">${value}</span>`;
			}
		}

		return value;
	}
};