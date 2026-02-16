frappe.query_reports["Doctor Commission Summary"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.month_start(),
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1,
    },
    { fieldname: "practitioner", label: __("Practitioner"), fieldtype: "Link", options: "Healthcare Practitioner" },
  ],
};
