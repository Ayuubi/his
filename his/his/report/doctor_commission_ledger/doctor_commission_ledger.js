frappe.query_reports["Doctor Commission Ledger"] = {
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

    {
      fieldname: "work_doctype",
      label: __("Work DocType"),
      fieldtype: "Select",
      options: ["", "Lab Result", "Radiology", "Clinical Procedure", "Sales Invoice"].join("\n"),
    },

    { fieldname: "source_order", label: __("Source Order"), fieldtype: "Data" },
    { fieldname: "item_group", label: __("Item Group"), fieldtype: "Link", options: "Item Group" },

    {
      fieldname: "status",
      label: __("Status"),
      fieldtype: "Select",
      options: ["", "Not Billed", "Draft", "Pending", "Paid", "Cancelled", "Reversed", "Unknown"].join("\n"),
    },
  ],
};
