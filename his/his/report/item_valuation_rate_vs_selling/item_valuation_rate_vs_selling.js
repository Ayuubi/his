// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Valuation Rate vs Selling"] = {
	"filters": [

        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company")
        },

        {
            fieldname: "price_list",
            label: __("Selling Price List"),
            fieldtype: "Link",
            options: "Price List",
            default: "Standard Selling",
            reqd: 1
        },

        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse",
            get_query: function() {

                let company =
                    frappe.query_report.get_filter_value("company");

                return {
                    filters: {
                        company: company,
                        is_group: 0
                    }
                };
            }
        },

        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
			default: "Drug"
        },

        {
            fieldname: "item_code",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item"
        },

        {
            fieldname: "price_status",
            label: __("Status"),
            fieldtype: "Select",
            options: [
                "All",
                "Problems",
                "LOSS",
                "BREAK EVEN",
                "LOW MARGIN",
                "NO SELLING PRICE",
                "OK"
            ].join("\n"),
            default: "All"
        },

        {
            fieldname: "minimum_margin",
            label: __("Minimum Margin %"),
            fieldtype: "Float",
            default: 10
        },

        {
            fieldname: "valuation_above_selling",
            label: __("Valuation > Selling Only"),
            fieldtype: "Check",
            default: 0
        },

        {
            fieldname: "only_with_stock",
            label: __("Only With Stock"),
            fieldtype: "Check",
            default: 1
        }

    ],


    formatter: function(
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


        // -------------------------------------
        // STATUS
        // -------------------------------------

        if (column.fieldname === "status") {

            if (data.status === "LOSS") {

                return `
                    <span style="
                        color:#c62828;
                        font-weight:700;
                    ">
                        🔴 LOSS
                    </span>
                `;
            }

            if (data.status === "BREAK EVEN") {

                return `
                    <span style="
                        color:#e65100;
                        font-weight:700;
                    ">
                        🟠 BREAK EVEN
                    </span>
                `;
            }

            if (data.status === "LOW MARGIN") {

                return `
                    <span style="
                        color:#ef6c00;
                        font-weight:700;
                    ">
                        🟠 LOW MARGIN
                    </span>
                `;
            }

            if (data.status === "NO SELLING PRICE") {

                return `
                    <span style="
                        color:#6a1b9a;
                        font-weight:700;
                    ">
                        ⚠ NO SELLING PRICE
                    </span>
                `;
            }

            return `
                <span style="
                    color:#2e7d32;
                    font-weight:700;
                ">
                    🟢 OK
                </span>
            `;
        }


        // -------------------------------------
        // SELLING RATE
        // -------------------------------------

        if (
            column.fieldname === "selling_rate"
            && data.status === "LOSS"
        ) {

            return `
                <span style="
                    color:#c62828;
                    font-weight:700;
                    background:#ffebee;
                    padding:3px 6px;
                    border-radius:4px;
                ">
                    ${value}
                </span>
            `;
        }


        // -------------------------------------
        // VALUATION
        // -------------------------------------

        if (
            column.fieldname === "valuation_rate"
            && data.status === "LOSS"
        ) {

            return `
                <span style="
                    color:#c62828;
                    font-weight:700;
                    background:#ffebee;
                    padding:3px 6px;
                    border-radius:4px;
                ">
                    ${value}
                </span>
            `;
        }


        // -------------------------------------
        // DIFFERENCE
        // -------------------------------------

        if (column.fieldname === "difference") {

            if (data.difference < 0) {

                return `
                    <span style="
                        color:#c62828;
                        font-weight:700;
                    ">
                        ${value}
                    </span>
                `;
            }

            return `
                <span style="
                    color:#2e7d32;
                    font-weight:600;
                ">
                    ${value}
                </span>
            `;
        }


        // -------------------------------------
        // MARGIN
        // -------------------------------------

        if (column.fieldname === "margin_percent") {

            if (data.status === "LOSS") {

                return `
                    <span style="
                        color:#c62828;
                        font-weight:700;
                    ">
                        ${value}
                    </span>
                `;
            }

            if (
                data.status === "BREAK EVEN"
                || data.status === "LOW MARGIN"
            ) {

                return `
                    <span style="
                        color:#ef6c00;
                        font-weight:700;
                    ">
                        ${value}
                    </span>
                `;
            }

            return `
                <span style="
                    color:#2e7d32;
                    font-weight:600;
                ">
                    ${value}
                </span>
            `;
        }


        return value;
    }
};