// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Attendance Range Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.month_start()
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.month_end()
		},
		{
			"fieldname": "view_type",
			"label": __("View Type"),
			"fieldtype": "Select",
			"options": "Detail\nSummary",
			"default": "Detail",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname": "status",
			"label": __("Attendance Status"),
			"fieldtype": "Select",
			"options": "\nPresent\nAbsent\nHalf Day\nOn Leave\nHoliday\nOff Day\nNo Schedule\nMissing Checkout"
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		if (data.is_total_row) {
			return `<b style="color: #111827;">${value || ""}</b>`;
		}

		if (column.fieldname === "attendance_status") {
			if (data.attendance_status === "Present") {
				value = `<span style="color: green; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "Absent") {
				value = `<span style="color: red; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "On Leave") {
				value = `<span style="color: #2563eb; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "Holiday") {
				value = `<span style="color: #6b7280; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "Off Day") {
				value = `<span style="color: #6b7280; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "No Schedule") {
				value = `<span style="color: #374151; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "Half Day") {
				value = `<span style="color: #d97706; font-weight: 600;">${value}</span>`;
			} else if (data.attendance_status === "Missing Checkout") {
				value = `<span style="color: #b45309; font-weight: 600;">${value}</span>`;
			}
		}

		if (
			column.fieldname === "late_in" ||
			column.fieldname === "total_late_in" ||
			column.fieldname === "late_out" ||
			column.fieldname === "total_late_out"
		) {
			if (value && value !== "0") {
				value = `<span style="color: #d97706; font-weight: 600;">${value}</span>`;
			}
		}

		if (
			column.fieldname === "early_in" ||
			column.fieldname === "total_early_in" ||
			column.fieldname === "early_out" ||
			column.fieldname === "total_early_out"
		) {
			if (value && value !== "0") {
				value = `<span style="color: #2563eb; font-weight: 600;">${value}</span>`;
			}
		}

		if (column.fieldname === "attendance_percentage") {
			let percent = flt(data.attendance_percentage || 0);

			if (percent >= 90) {
				value = `<span style="color: green; font-weight: 600;">${value}</span>`;
			} else if (percent >= 70) {
				value = `<span style="color: #d97706; font-weight: 600;">${value}</span>`;
			} else {
				value = `<span style="color: red; font-weight: 600;">${value}</span>`;
			}
		}

		return value;
	}
};