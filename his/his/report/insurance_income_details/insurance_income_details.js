// Copyright (c) 2026, Shaafi Hospital
// For license information, please see license.txt

frappe.query_reports["Insurance Income Details"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "view",
			label: __("View"),
			fieldtype: "Select",
			options: [
				"Income Summary",
				"Item Group Summary",
				"Invoice Details",
				"Unallocated Journals",
			].join("\n"),
			default: "Income Summary",
			reqd: 1,
			on_change: function () {
				toggle_filters();
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "insurance",
			label: __("Insurance"),
			fieldtype: "Link",
			options: "Customer",
			get_query: function () {
				return {
					filters: {
						customer_group: "Insurance",
					},
				};
			},
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "income_account",
			label: __("Income Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				const company =
					frappe.query_report.get_filter_value("company");

				return {
					filters: {
						company: company,
						root_type: "Income",
						is_group: 0,
					},
				};
			},
		},
		{
			fieldname: "patient",
			label: __("Patient"),
			fieldtype: "Link",
			options: "Patient",
		},
		{
			fieldname: "sales_invoice",
			label: __("Sales Invoice"),
			fieldtype: "Link",
			options: "Sales Invoice",
		},
		{
			fieldname: "journal_entry",
			label: __("Journal Entry"),
			fieldtype: "Link",
			options: "Journal Entry",
		},
		{
			fieldname: "status",
			label: __("Transfer Status"),
			fieldtype: "Select",
			options: [
				"",
				"Allocated",
				"Not Transferred",
			].join("\n"),
		},
	],

	onload: function (report) {
		toggle_filters();

		report.page.add_inner_button(
			__("Show Invoice Details"),
			function () {
				report.set_filter_value("view", "Invoice Details");
			},
			__("View")
		);

		report.page.add_inner_button(
			__("Show Unallocated Journals"),
			function () {
				report.set_filter_value(
					"view",
					"Unallocated Journals"
				);
			},
			__("View")
		);
	},

	formatter: function (
		value,
		row,
		column,
		data,
		default_formatter
	) {
		value = default_formatter(
			value,
			row,
			column,
			data
		);

		if (!data) {
			return value;
		}

		if (
			data.is_month_total ||
			data.is_grand_total
		) {
			value = `<strong>${value || ""}</strong>`;
		}

		if (
			column.fieldname === "transfer_status"
		) {
			if (data.transfer_status === "Allocated") {
				value = `<span class="indicator-pill green">
					${__("Allocated")}
				</span>`;
			}

			if (
				data.transfer_status ===
				"Not Transferred"
			) {
				value = `<span class="indicator-pill orange">
					${__("Not Transferred")}
				</span>`;
			}
		}

		if (
			column.fieldname === "reason" &&
			data.reason
		) {
			value = `<span class="indicator-pill red">
				${frappe.utils.escape_html(data.reason)}
			</span>`;
		}

		return value;
	},
};


function toggle_filters() {
	const view =
		frappe.query_report.get_filter_value("view");

	const item_filters = [
		"item_group",
		"income_account",
		"patient",
		"sales_invoice",
		"status",
	];

	const journal_filters = [
		"journal_entry",
	];

	const is_unallocated =
		view === "Unallocated Journals";

	item_filters.forEach(function (fieldname) {
		const filter =
			frappe.query_report.get_filter(fieldname);

		if (filter) {
			filter.toggle(!is_unallocated);
		}
	});

	journal_filters.forEach(function (fieldname) {
		const filter =
			frappe.query_report.get_filter(fieldname);

		if (filter) {
			filter.toggle(is_unallocated);
		}
	});
}