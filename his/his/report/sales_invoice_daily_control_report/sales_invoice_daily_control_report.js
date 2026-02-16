// frappe.query_reports["Sales Invoice Daily Control Report"] = {
//   filters: [
//     { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
//     { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },

//     { fieldname: "status", label: __("Status"), fieldtype: "Select", options: ["", "Paid", "Credit", "Return", "Cancelled"] },

//     { fieldname: "invoice", label: __("Invoice"), fieldtype: "Link", options: "Sales Invoice" },
//     { fieldname: "patient", label: __("Patient"), fieldtype: "Link", options: "Patient" },
//     { fieldname: "doctor", label: __("Doctor"), fieldtype: "Link", options: "Healthcare Practitioner" },

//     // renamed cashier filter to created_by
//     { fieldname: "created_by", label: __("Created By"), fieldtype: "Link", options: "User" },

//     { fieldname: "only_discounted", label: __("Only Discounted"), fieldtype: "Check", default: 0 },

//     { fieldname: "row_limit", label: __("Max Rows"), fieldtype: "Int", default: 1500 }
//   ]
// };
frappe.query_reports["Sales Invoice Daily Control Report"] = {
  filters: [
    { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
    { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },

    { fieldname: "status", label: __("Status"), fieldtype: "Select", options: ["", "Paid", "Credit", "Return", "Cancelled"] },

    { fieldname: "invoice", label: __("Invoice"), fieldtype: "Link", options: "Sales Invoice" },
    { fieldname: "patient", label: __("Patient"), fieldtype: "Link", options: "Patient" },
    { fieldname: "doctor", label: __("Doctor"), fieldtype: "Link", options: "Healthcare Practitioner" },
    { fieldname: "created_by", label: __("Created By"), fieldtype: "Link", options: "User" },

    { fieldname: "only_discounted", label: __("Only Discounted"), fieldtype: "Check", default: 0 },

    // Make it small while we stabilize UI
    { fieldname: "row_limit", label: __("Max Rows"), fieldtype: "Int", default: 200 }
  ],

  formatter(value, row, column, data, default_formatter) {
    const v = default_formatter(value, row, column, data);

    if (!data) return v;

    if (column.fieldname === "inv_status") {
      const s = (data.inv_status || "").toString();

      // very cheap mapping
      let color = "gray";
      if (s === "Paid") color = "green";
      else if (s === "Credit") color = "orange";
      else if (s === "Return") color = "blue";
      else if (s === "Cancelled") color = "red";

      // avoid extra function calls
      return `<span class="indicator-pill ${color}">${s || "-"}</span>`;
    }

    return v;
  },

  get_datatable_options(options) {
    // IMPORTANT: disable dynamic row height (this often causes freezes with long remarks)
    return Object.assign(options, {
      dynamicRowHeight: false,
      cellHeight: 32,
    });
  },
};
