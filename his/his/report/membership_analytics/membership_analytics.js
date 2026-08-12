// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Membership Analytics"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "view_type",
            label: __("View Type"),
            fieldtype: "Select",
            options: [
                "Membership Summary",
                "Old vs New Detail",
                "Usage Summary",
                "Usage Detail"
            ],
            default: "Membership Summary",
            reqd: 1
        },
        {
            fieldname: "membership_status",
            label: __("Membership Status"),
            fieldtype: "Select",
            options: "\nActive\nInactive",
            default: "Active"
        },
        {
            fieldname: "discount_level",
            label: __("Discount Level"),
            fieldtype: "Select",
            options: "\n15\n20\n25\n30\n50\n70"
        },
        {
            fieldname: "card_number",
            label: __("Card Number"),
            fieldtype: "Int"
        },
        {
            fieldname: "patient",
            label: __("Patient"),
            fieldtype: "Link",
            options: "Patient"
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
            depends_on: "eval:doc.view_type == 'Usage Detail'"
        },
        {
            fieldname: "show_only_used",
            label: __("Show Only Used Members"),
            fieldtype: "Check",
            default: 0,
            depends_on: "eval:doc.view_type == 'Old vs New Detail'"
        }
    ]
};