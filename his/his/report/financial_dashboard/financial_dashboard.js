/**
 * Financial Dashboard — Frappe Script Report (JS)
 * =================================================
 * Module      : Accounts
 * Ref DocType : Sales Invoice
 *
 * Filters:
 *   - From Date / To Date  (required)
 *   - Company
 *   - Cost Center
 *   - Finance Book
 *   - Currency
 *
 * Sections rendered via Python message HTML:
 *   1. P&L Summary Cards        (Income / Expense / Net Profit)
 *   2. P&L Monthly Chart        (bar + line, from GL)
 *   3. P&L Accounts Breakdown   (income & expense per account with donut charts)
 *   4. AR Summary Card          (GL-based, includes journal + payment entries)
 *   5. Top 10 AR Table          (GL party balance)
 *   6. AP Summary Card          (GL-based, includes journal + payment entries)
 *   7. Top 10 AP Table          (GL party balance)
 */

frappe.query_reports["Financial Dashboard"] = {

    /* ── FILTERS ─────────────────────────────────────────────────────── */
    filters: [
        {
            fieldname : "from_date",
            label     : __("From Date"),
            fieldtype : "Date",
            default   : frappe.datetime.month_start(), 
            reqd      : 1,
        },
        {
            fieldname : "to_date",
            label     : __("To Date"),
            fieldtype : "Date",
            default   : frappe.datetime.now_date(),
            reqd      : 1,
        },
        {
            fieldname : "company",
            label     : __("Company"),
            fieldtype : "Link",
            options   : "Company",
            default   : frappe.defaults.get_user_default("Company"),
            reqd      : 1,
        },
        {
            fieldname : "cost_center",
            label     : __("Cost Center"),
            fieldtype : "Link",
            options   : "Cost Center",
            get_query : () => ({
                filters: {
                    company  : frappe.query_report.get_filter_value("company") || "",
                    is_group : 0,
                }
            }),
        },
        {
            fieldname : "finance_book",
            label     : __("Finance Book"),
            fieldtype : "Link",
            options   : "Finance Book",
        },
        {
            fieldname : "currency",
            label     : __("Presentation Currency"),
            fieldtype : "Link",
            options   : "Currency",
            default   : frappe.boot.sysdefaults && frappe.boot.sysdefaults.currency,
        },
    ],

    /* ── FORMATTER ───────────────────────────────────────────────────── */
    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        // Outstanding amount — red when positive
        if (column.fieldname === "outstanding_amount") {
            const num = parseFloat(
                (data[column.fieldname] || "").toString().replace(/[^0-9.-]/g, "")
            ) || 0;
            if (num > 0) {
                return `<span style="color:#dc2626;font-weight:700;
                    font-family:'DM Mono',monospace">${value}</span>`;
            }
        }

        // Status pill
        if (column.fieldname === "status" && data.status) {
            const map = {
                "Paid"        : { bg: "#d1fae5", fg: "#065f46" },
                "Unpaid"      : { bg: "#eff6ff", fg: "#1d4ed8" },
                "Partly Paid" : { bg: "#fef3c7", fg: "#92400e" },
                "Overdue"     : { bg: "#fee2e2", fg: "#991b1b" },
                "Cancelled"   : { bg: "#f3f4f6", fg: "#6b7280" },
                "Return"      : { bg: "#f5f3ff", fg: "#5b21b6" },
                "Draft"       : { bg: "#f1f5f9", fg: "#64748b" },
            };
            const s = map[data.status];
            if (s) {
                return `<span style="display:inline-flex;align-items:center;gap:5px;
                    padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;
                    background:${s.bg};color:${s.fg}">
                    <span style="width:5px;height:5px;border-radius:50%;
                        background:${s.fg};display:inline-block"></span>
                    ${data.status}</span>`;
            }
        }

        // Ageing / due_days
        if (column.fieldname === "due_days") {
            const days = parseInt(data.due_days) || 0;
            if (days <= 0)  return `<span style="color:#059669;font-weight:600">Current</span>`;
            if (days <= 15) return `<span style="color:#d97706;font-weight:600">${days}d</span>`;
            if (days <= 30) return `<span style="color:#ea580c;font-weight:600">${days}d</span>`;
            return `<strong style="color:#dc2626">${days}d OVERDUE</strong>`;
        }

        return value;
    },

    /* ── ON LOAD ─────────────────────────────────────────────────────── */
    onload(report) {

        /* ── Quick date presets ─────────────────────────────────────── */
        const presets = [
            {
                label : __("This Month"),
                fn() {
                    report.set_filter_value("from_date", frappe.datetime.month_start());
                    report.set_filter_value("to_date",   frappe.datetime.month_end());
                },
            },
            {
                label : __("Last Month"),
                fn() {
                    const s = frappe.datetime.add_months(frappe.datetime.month_start(), -1);
                    report.set_filter_value("from_date", s);
                    report.set_filter_value("to_date",   frappe.datetime.month_end(s));
                },
            },
            {
                label : __("This Quarter"),
                fn() {
                    report.set_filter_value("from_date", frappe.datetime.quarter_start());
                    report.set_filter_value("to_date",   frappe.datetime.quarter_end());
                },
            },
            {
                label : __("Last Quarter"),
                fn() {
                    const qs = frappe.datetime.add_months(frappe.datetime.quarter_start(), -3);
                    const qe = frappe.datetime.add_months(frappe.datetime.quarter_end(),   -3);
                    report.set_filter_value("from_date", qs);
                    report.set_filter_value("to_date",   qe);
                },
            },
            {
                label : __("This Year"),
                fn() {
                    report.set_filter_value("from_date", frappe.datetime.year_start());
                    report.set_filter_value("to_date",   frappe.datetime.now_date());
                },
            },
            {
                label : __("Last Year"),
                fn() {
                    const ys = frappe.datetime.add_months(frappe.datetime.year_start(), -12);
                    const ye = frappe.datetime.add_months(frappe.datetime.year_end(),   -12);
                    report.set_filter_value("from_date", ys);
                    report.set_filter_value("to_date",   ye);
                },
            },
        ];

        presets.forEach(p => {
            report.page.add_inner_button(p.label, () => {
                p.fn();
                report.refresh();
            });
        });

        /* ── Print helper ───────────────────────────────────────────── */
        report.page.add_inner_button(__("🖨️ Print Report"), () => {
            window.print();
        });
    },

    /* ── AFTER RENDER ────────────────────────────────────────────────── */
    after_datatable_render(datatable) {
        // Highlight any summary / total rows
        document.querySelectorAll(".dt-row").forEach(row => {
            const cell = row.querySelector(".dt-cell");
            if (cell && cell.innerText && cell.innerText.trim() === "Total") {
                row.style.background = "#f8f9fb";
                row.style.fontWeight = "700";
                row.style.borderTop  = "2px solid #e4e8ef";
            }
        });
    },
};
