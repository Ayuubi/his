// Copyright (c) 2026
// License: MIT

frappe.query_reports["Sales and Collection Analysis"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
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
            fieldname: "view",
            label: __("View"),
            fieldtype: "Select",
            options: [
                "Daily Summary",
                "Collection Details",
                "Sales Settlement Details",
                "Discount Details",
                "Return Details"
            ],
            default: "Daily Summary",
            reqd: 1,
            on_change: function () {
                frappe.query_report.refresh();
            }
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "customer_group",
            label: __("Customer Group"),
            fieldtype: "Link",
            options: "Customer Group"
        },
        {
            fieldname: "classification",
            label: __("Cash Source"),
            fieldtype: "Select",
            options: [
                "All",
                "Today's Sales",
                "Previous Invoice",
                "Unallocated"
            ],
            default: "All"
        },
        {
            fieldname: "settlement_filter",
            label: __("Settlement Filter"),
            fieldtype: "Select",
            options: [
                "All",
                "Outstanding Only",
                "Discounted Only",
                "Returned Only"
            ],
            default: "All"
        },
        {
            fieldname: "discount_category",
            label: __("Discount Category"),
            fieldtype: "Select",
            options: [
                "All",
                "Today's Sales",
                "Previous Invoice",
                "Unallocated"
            ],
            default: "All"
        },
        {
            fieldname: "return_link_status",
            label: __("Return Link Status"),
            fieldtype: "Select",
            options: [
                "All",
                "Linked Only",
                "Unlinked Only"
            ],
            default: "All"
        },
        {
            fieldname: "payment_entry",
            label: __("Payment Entry"),
            fieldtype: "Link",
            options: "Payment Entry"
        },
        {
            fieldname: "sales_invoice",
            label: __("Sales Invoice"),
            fieldtype: "Link",
            options: "Sales Invoice"
        },
        {
            fieldname: "mode_of_payment",
            label: __("Mode of Payment"),
            fieldtype: "Link",
            options: "Mode of Payment"
        },
        {
            fieldname: "collection_account",
            label: __("Collection Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: function () {
                return {
                    filters: {
                        company: frappe.query_report.get_filter_value("company"),
                        is_group: 0
                    }
                };
            }
        },
        {
            fieldname: "collected_by",
            label: __("Collected By"),
            fieldtype: "Link",
            options: "User"
        }
    ],

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

        if (data.is_total_row) {
            value = `<strong>${value}</strong>`;
        }

        if (column.fieldname === "classification") {
            if (data.classification === "Today's Sales") {
                value = `<span class="indicator-pill green">${value}</span>`;
            } else if (data.classification === "Previous Invoice") {
                value = `<span class="indicator-pill blue">${value}</span>`;
            } else if (data.classification === "Unallocated") {
                value = `<span class="indicator-pill orange">${value}</span>`;
            }
        }

        if (
            column.fieldname === "outstanding_at_day_end" &&
            flt(data.outstanding_at_day_end) > 0
        ) {
            value = `<span class="text-danger">${value}</span>`;
        }

        return value;
    }
};