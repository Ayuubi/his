// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pharmacy Unified Price Comparison"] = {
	filters: [
        {
            fieldname: "buying_price_list",
            label: __("Buying Price List"),
            fieldtype: "Link",
            options: "Price List",
            reqd: 1,
            get_query: function () {
                return {
                    filters: {
                        buying: 1
                    }
                };
            },
			default: "Standard Buying",
        },
        {
            fieldname: "selling_price_list",
            label: __("Selling Price List"),
            fieldtype: "Link",
            options: "Price List",
            reqd: 1,
            get_query: function () {
                return {
                    filters: {
                        selling: 1
                    }
                };
            },
			default: "Standard Selling",
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
            default: "Drug"
        },
        {
            fieldname: "brand",
            label: __("Brand"),
            fieldtype: "Link",
            options: "Brand",
			hidden: 1
        },
        {
            fieldname: "item",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "show_only_with_both_prices",
            label: __("Show Only With Both Prices"),
            fieldtype: "Check",
            default: 0,
			hidden: 1
        },
        {
            fieldname: "show_only_ok_rows",
            label: __("Show Only OK Rows"),
            fieldtype: "Check",
            default: 0,
			hidden: 1
        }
    ]
};
