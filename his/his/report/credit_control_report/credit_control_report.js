/* eslint-disable */

frappe.query_reports["Credit Control Report"] = {
  filters: [
    { fieldname: "from_date", label: "From Date", fieldtype: "Date", default: frappe.datetime.get_today(), },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date", default: frappe.datetime.get_today(), },

    { fieldname: "company", label: "Company", fieldtype: "Link", options: "Company", default: "Shaafi Hospital", },
    { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" },

    {
      fieldname: "patient_id",
      label: "Patient ID",
      fieldtype: "Data",
      placeholder: "e.g. SHP-547681",
    },

    {
      fieldname: "changed_by",
      label: "Changed By (User)",
      fieldtype: "Link",
      options: "User",
      on_change: function () {
        const user = frappe.query_report.get_filter_value("changed_by");
        if (!user) {
          frappe.query_report.set_filter_value("changed_by_name", "");
          return;
        }

        // fetch user's full_name and auto fill
        frappe.db.get_value("User", user, "full_name").then((r) => {
          frappe.query_report.set_filter_value("changed_by_name", r?.message?.full_name || "");
        });
      },
    },

    {
      fieldname: "changed_by_name",
      label: "Changed By Name",
      fieldtype: "Data",
      read_only: 1,
    },
	{
		fieldname: "limit",
		label: "Max Rows",
		fieldtype: "Int",
		default: 2000
	},
  ],

  onload: function () {
    // if report loads with changed_by already set (saved filters), auto fill name
    const user = frappe.query_report.get_filter_value("changed_by");
    if (user) {
      frappe.db.get_value("User", user, "full_name").then((r) => {
        frappe.query_report.set_filter_value("changed_by_name", r?.message?.full_name || "");
      });
    }
  },
};