// Copyright (c) 2026, Rasiin Tech
// For license information, please see license.txt

frappe.query_reports["Daily POS Bank Transfer Reconciliation"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
            on_change: function () {
                frappe.query_report.set_filter_value(
                    "main_merchant_account",
                    ""
                );

                frappe.query_report.set_filter_value(
                    "account",
                    ""
                );
            },
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "main_merchant_account",
            label: __("Final Main Merchant Account"),
            fieldtype: "Link",
            options: "Account",
            reqd: 1,
            get_query: function () {
                return {
                    filters: {
                        company:
                            frappe.query_report.get_filter_value(
                                "company"
                            ),
                        is_group: 0,
                        account_type: ["in", ["Cash", "Bank"]],
                    },
                };
            },
        },
        {
            fieldname: "account",
            label: __("Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: function () {
                return {
                    filters: {
                        company:
                            frappe.query_report.get_filter_value(
                                "company"
                            ),
                        is_group: 0,
                        account_type: ["in", ["Cash", "Bank"]],
                    },
                };
            },
        },
        {
            fieldname: "account_role",
            label: __("Account Role"),
            fieldtype: "Select",
            options: [
                "",
                "POS Merchant",
                "Main Merchant",
                "Bank Account",
            ].join("\n"),
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: [
                "",
                "Closed",
                "Partially Closed",
                "Not Closed",
                "Settled",
                "Partially Settled",
                "Pending Bank Transfer",
                "Excess Transfer",
                "Received by Bank",
                "Bank Activity",
                "Variance",
                "No Activity",
            ].join("\n"),
        },
        {
            fieldname: "exceptions_only",
            label: __("Exceptions Only"),
            fieldtype: "Check",
            default: 0,
        },
        {
            fieldname: "show_zero_activity",
            label: __("Show Accounts Without Activity"),
            fieldtype: "Check",
            default: 0,
        },
    ],

    formatter: function (
        value,
        row,
        column,
        data,
        default_formatter
    ) {
        if (!data) {
            return default_formatter(
                value,
                row,
                column,
                data
            );
        }

        const formatted_value = default_formatter(
            value,
            row,
            column,
            data
        );

        if (column.fieldname === "account_role") {
            const role_colors = {
                "POS Merchant": "blue",
                "Main Merchant": "purple",
                "Bank Account": "green",
            };

            const color =
                role_colors[data.account_role] || "gray";

            return `
                <span class="indicator-pill ${color}">
                    ${frappe.utils.escape_html(
                        data.account_role || ""
                    )}
                </span>
            `;
        }

        if (column.fieldname === "status") {
            const status_colors = {
                "Closed": "green",
                "Settled": "green",
                "Received by Bank": "green",

                "Partially Closed": "orange",
                "Partially Settled": "orange",
                "Excess Transfer": "orange",
                "Bank Activity": "blue",

                "Not Closed": "red",
                "Pending Bank Transfer": "red",
                "Variance": "red",

                "No Activity": "gray",
            };

            const color =
                status_colors[data.status] || "gray";

            return `
                <span class="indicator-pill ${color}">
                    ${frappe.utils.escape_html(
                        data.status || ""
                    )}
                </span>
            `;
        }

        if (
            column.fieldname === "pending_transfer"
            && flt(data.pending_transfer || 0) > 0.009
        ) {
            return `
                <span style="
                    color: var(--red-600);
                    font-weight: 700;
                ">
                    ${formatted_value}
                </span>
            `;
        }

        if (
            column.fieldname === "excess_transfer"
            && flt(data.excess_transfer || 0) > 0.009
        ) {
            return `
                <span style="
                    color: var(--orange-600);
                    font-weight: 700;
                ">
                    ${formatted_value}
                </span>
            `;
        }

        if (column.fieldname === "transfer_variance") {
            const variance = flt(
                data.transfer_variance || 0
            );

            if (variance < -0.009) {
                return `
                    <span style="
                        color: var(--red-600);
                        font-weight: 700;
                    ">
                        ${formatted_value}
                    </span>
                `;
            }

            if (variance > 0.009) {
                return `
                    <span style="
                        color: var(--orange-600);
                        font-weight: 700;
                    ">
                        ${formatted_value}
                    </span>
                `;
            }

            return `
                <span style="
                    color: var(--green-600);
                    font-weight: 700;
                ">
                    ${formatted_value}
                </span>
            `;
        }

        if (
            [
                "net_collections",
                "received_from_merchants",
                "transferred_to_main",
                "transferred_to_bank",
                "actual_transfer",
            ].includes(column.fieldname)
            && Math.abs(
                flt(data[column.fieldname] || 0)
            ) > 0.009
        ) {
            return `
                <span style="font-weight: 600;">
                    ${formatted_value}
                </span>
            `;
        }

        return formatted_value;
    },

    onload: function (report) {
        report.page.add_inner_button(
            __("Show Exceptions"),
            function () {
                report.set_filter_value(
                    "exceptions_only",
                    1
                );

                report.refresh();
            }
        );

        report.page.add_inner_button(
            __("Show All"),
            function () {
                report.set_filter_value(
                    "exceptions_only",
                    0
                );

                report.set_filter_value(
                    "account",
                    ""
                );

                report.set_filter_value(
                    "account_role",
                    ""
                );

                report.set_filter_value(
                    "status",
                    ""
                );

                report.refresh();
            }
        );

        report.page.add_inner_button(
            __("Main Merchant Only"),
            function () {
                report.set_filter_value(
                    "account_role",
                    "Main Merchant"
                );

                report.refresh();
            }
        );

        report.page.add_inner_button(
            __("POS Merchants Only"),
            function () {
                report.set_filter_value(
                    "account_role",
                    "POS Merchant"
                );

                report.refresh();
            }
        );
    },
};