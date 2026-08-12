// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Low Stock Alert"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: function () {
				let filters = {
					is_group: 0
				};

				let company = frappe.query_report.get_filter_value("company");
				if (company) {
					filters.company = company;
				}

				return {
					filters: filters
				};
			}
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group"
		},
		{
			fieldname: "material_request_type",
			label: __("Material Request Type"),
			fieldtype: "Select",
			options: "\nPurchase\nMaterial Transfer\nMaterial Issue\nManufacture"
		},
		{
			fieldname: "show_only_low_stock",
			label: __("Show Only Low Stock"),
			fieldtype: "Check",
			default: 1
		}
	],

	onload: function (report) {
		report.page.add_inner_button(__("Create Material Request"), function () {
			frappe.confirm(
				__("Create Draft Material Request from current Low Stock Alert rows?"),
				function () {
					frappe.call({
						method: "his.his.report.low_stock_alert.low_stock_alert.create_material_request",
						args: {
							filters: frappe.query_report.get_filter_values()
						},
						freeze: true,
						freeze_message: __("Creating Material Request..."),
						callback: function (r) {
							if (!r.message) {
								return;
							}

							let created = r.message.material_requests || [];
							let skipped = r.message.skipped || [];
							let html = "";

							if (created.length) {
								html += `<p><b>${__("Created Material Request")}:</b></p>`;
								html += "<ul>";

								created.forEach(function (name) {
									let safe_name = frappe.utils.escape_html(name);
									html += `<li><a href="/app/material-request/${encodeURIComponent(name)}">${safe_name}</a></li>`;
								});

								html += "</ul>";
							}

							if (skipped.length) {
								html += `<hr><p><b>${__("Skipped Items")}:</b></p>`;
								html += "<ul>";

								skipped.forEach(function (row) {
									let item_code = frappe.utils.escape_html(row.item_code || "");
									let warehouse = frappe.utils.escape_html(row.warehouse || "");
									let reason = frappe.utils.escape_html(row.reason || "");
									let existing_request = row.existing_request
										? ` - ${__("Existing")}: ${frappe.utils.escape_html(row.existing_request)}`
										: "";

									html += `<li>${item_code} / ${warehouse} - ${reason}${existing_request}</li>`;
								});

								html += "</ul>";
							}

							if (!html) {
								html = __("No Material Request was created.");
							}

							frappe.msgprint({
								title: __("Low Stock Alert"),
								message: html,
								indicator: created.length ? "green" : "orange"
							});

							frappe.query_report.refresh();

							if (created.length === 1) {
								frappe.set_route("Form", "Material Request", created[0]);
							}
						}
					});
				}
			);
		});
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		if (column.fieldname === "status") {
			let color = "green";

			if (data.status === "Out of Stock") {
				color = "red";
			} else if (data.status === "Critical") {
				color = "orange";
			} else if (data.status === "Need Reorder") {
				color = "blue";
			} else if (data.status === "Low Stock / Ordered") {
				color = "yellow";
			}

			return `<span class="indicator-pill ${color}">${value}</span>`;
		}

		if (
			["actual_qty", "projected_qty", "reorder_level"].includes(column.fieldname)
			&& flt(data.actual_qty) <= flt(data.reorder_level)
		) {
			return `<b>${value}</b>`;
		}

		return value;
	}
};