frappe.query_reports["Customer Group Discount Analysis"] = {
    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
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
            fieldname: "report_type",
            label: "Report Type",
            fieldtype: "Select",
            options: "Detail\nSummary",
            default: "Detail",
            reqd: 1
        },
        {
            fieldname: "customer_group",
            label: "Customer Group",
            fieldtype: "Link",
            options: "Customer Group"
        },
        {
            fieldname: "item_group",
            label: "Item Group",
            fieldtype: "Link",
            options: "Item Group"
        }
    ]
};