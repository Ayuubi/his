// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pharmacy Consumption & Reorder Planning Report"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": "Company",
            "fieldtype": "Link",
            "options": "Company",
			"default": "Shaafi Hospital"
        },
        {
            "fieldname": "warehouse",
            "label": "Warehouse",
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "period",
            "label": "Period",
            "fieldtype": "Select",
            "options": "\nWeekly\nMonthly\nQuarterly",
            "default": "Weekly",
            "reqd": 1
        },
        {
            "fieldname": "as_on_date",
            "label": "As On Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "item_group",
            "label": "Item Group",
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "item_code",
            "label": "Item",
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "status",
            "label": "Status",
            "fieldtype": "Select",
            "options": "\nOut of Stock\nBelow Minimum\nBelow Reorder\nNormal\nOverstock"
        },
        {
            "fieldname": "only_reorder_items",
            "label": "Show Only Reorder Items",
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "top_fast_moving",
            "label": "Top Fast Moving Only",
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "top_n",
            "label": "Top N",
            "fieldtype": "Int",
            "default": 20,
            "depends_on": "eval:doc.top_fast_moving==1"
        }
    ]
};