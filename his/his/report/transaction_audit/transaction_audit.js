// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Transaction Audit"] = {
	filters: [
		{
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            default: "Shaafi Hospital",
            reqd: 1,
            on_change: function () {
                frappe.query_report.set_filter_value("cost_center", "");
            }
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "cost_center",
            label: "Cost Center",
            fieldtype: "Link",
            options: "Cost Center",
            get_query: function () {
                const company = frappe.query_report.get_filter_value("company");
                return {
                    filters: {
                        company: company
                    }
                };
            },
			hidden: 1
        },
        {
            fieldname: "sales_type",
            label: "Sales Type",
            fieldtype: "Select",
            options: "\nCashiers\nPharmacy"
        },
        {
            fieldname: "user",
            label: "User",
            fieldtype: "Link",
            options: "User",
            on_change: function () {
                const user = frappe.query_report.get_filter_value("user");
                if (!user) {
                    frappe.query_report.set_filter_value("user_name", "");
                    return;
                }

                frappe.db.get_value("User", user, "full_name").then(r => {
                    frappe.query_report.set_filter_value("user_name", (r.message && r.message.full_name) || "");
                });
            }
        },
        {
            fieldname: "user_name",
            label: "User Name",
            fieldtype: "Data",
            read_only: 1
        },
        {
            fieldname: "status",
            label: "Status",
            fieldtype: "Select",
            options: "\nPaid\nUnpaid\nOverdue\nDraft\nCancelled"
        },
        {
            fieldname: "return_only",
            label: "Return Only",
            fieldtype: "Check",
            default: 0
        },
        {
            fieldname: "include_draft",
            label: "Include Draft",
            fieldtype: "Check",
            default: 0
        },
        {
            fieldname: "include_cancelled",
            label: "Include Cancelled",
            fieldtype: "Check",
            default: 0
        },
        {
            fieldname: "view_type",
            label: "View Type",
            fieldtype: "Select",
            options: "Summary\nDetailed",
            default: "Summary",
            reqd: 1
        }
    ]
};
