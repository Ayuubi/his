// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Canteen Report"] = {
	"filters": [
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
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
            get_query: function() {
                return {
                    filters: {
                        status: "Active"
                    }
                };
            }
        },
		{
            fieldname: "detailed_view",
            label: __("Detailed View"),
            fieldtype: "Check",
            default: 0,
            description: __("Check this box to see detailed transactions.")
        }
    ],
};
