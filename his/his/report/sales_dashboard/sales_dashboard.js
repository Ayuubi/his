/**
 * Sales Dashboard — Comprehensive Script Report (JS)
 * Filters: User, Cost Center, Sales Order Type, From Date, To Date
 *          + Company, Customer, Territory, Status
 */

frappe.query_reports["Sales Dashboard"] = {

    filters: [
        {
            fieldname: "from_date", label: __("From Date"), fieldtype: "Date",
            default: frappe.datetime.month_start(), reqd: 1,
        },
        {
            fieldname: "to_date", label: __("To Date"), fieldtype: "Date",
            default: frappe.datetime.month_end(), reqd: 1,
        },
        {
            fieldname: "company", label: __("Company"), fieldtype: "Link",
            options: "Company", default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "user", label: __("User"), fieldtype: "Link",
            options: "User",
            get_query: () => ({ filters: { enabled: 1 } }),
        },
        {
            fieldname: "cost_center", label: __("Cost Center"), fieldtype: "Link",
            options: "Cost Center",
            get_query: () => ({
                filters: {
                    company: frappe.query_report.get_filter_value("company") || "",
                    is_group: 0,
                }
            }),
        },
        {
            fieldname: "so_type", label: __("Sales Type"), fieldtype: "Link",
            options: "Sales Type",
        },
        {
            fieldname: "customer", label: __("Customer"), fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "territory", label: __("Territory"), fieldtype: "Link",
            options: "Territory",
        },
        {
            fieldname: "status", label: __("Status"), fieldtype: "Select",
            options: "\nPaid\nUnpaid\nPartly Paid\nOverdue\nCancelled\nReturn",
        },
    ],

    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        if (column.fieldname === "status" && data.status) {
            const map = {
                "Paid":        { bg: "#d1fae5", fg: "#065f46" },
                "Unpaid":      { bg: "#eff6ff", fg: "#1d4ed8" },
                "Partly Paid": { bg: "#fef3c7", fg: "#92400e" },
                "Overdue":     { bg: "#fee2e2", fg: "#991b1b" },
                "Cancelled":   { bg: "#f3f4f6", fg: "#6b7280" },
                "Return":      { bg: "#f5f3ff", fg: "#5b21b6" },
                "Draft":       { bg: "#f1f5f9", fg: "#64748b" },
            };
            const s = map[data.status];
            if (s) return `<span style="display:inline-flex;align-items:center;gap:5px;
                padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;
                background:${s.bg};color:${s.fg}">
                <span style="width:5px;height:5px;border-radius:50%;background:${s.fg};display:inline-block"></span>
                ${data.status}</span>`;
        }

        if (column.fieldname === "outstanding_amount") {
            const amt = parseFloat(data.outstanding_amount) || 0;
            if (amt === 0)   return `<span style="color:#28a745;font-weight:600">${value}</span>`;
            if (data.status === "Overdue") return `<strong style="color:#dc2626">${value}</strong>`;
        }

        if (column.fieldname === "grand_total")
            return `<strong style="color:#1f272e">${value}</strong>`;

        if (column.fieldname === "net_total")
            return `<span style="color:#17a2b8;font-weight:600">${value}</span>`;

        return value;
    },

    onload(report) {
        const setDates = (from, to) => {
            report.set_filter_value("from_date", from);
            report.set_filter_value("to_date", to);
        };

        [
            [__("Today"),         () => setDates(frappe.datetime.now_date(), frappe.datetime.now_date())],
            [__("This Week"),     () => setDates(frappe.datetime.week_start(), frappe.datetime.week_end())],
            [__("Last Month"),    () => { const s = frappe.datetime.add_months(frappe.datetime.month_start(), -1); setDates(s, frappe.datetime.month_end(s)); }],
            [__("This Month"),    () => setDates(frappe.datetime.month_start(), frappe.datetime.month_end())],
            [__("This Quarter"),  () => setDates(frappe.datetime.quarter_start(), frappe.datetime.quarter_end())],
            [__("This Year"),     () => setDates(frappe.datetime.year_start(), frappe.datetime.now_date())],
        ].forEach(([label, fn]) => {
            report.page.add_inner_button(label, () => { fn(); report.refresh(); });
        });
    },
};
