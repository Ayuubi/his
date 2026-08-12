// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Discount Tracking Report"] = {
  filters: [
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
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
      fieldname: "voucher_type",
      label: "Voucher Type",
      fieldtype: "Select",
      options: "\nAll\nPayment Entry\nJournal Entry",
      default: "All"
    },
    {
      fieldname: "view_type",
      label: "View Type",
      fieldtype: "Select",
      options: "Management Summary\nItem Group Summary\nItem Wise\nDetail",
      default: "Management Summary"
    },
    {
      fieldname: "chart_by",
      label: "Chart By",
      fieldtype: "Select",
      options: "Item Group\nItem\nSource\nCustomer Group\nDoctor",
      default: "Item Group"
    },
    {
      fieldname: "company",
      label: "Company",
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company")
    },
    {
      fieldname: "discount_account",
      label: "Discount Account",
      fieldtype: "Link",
      options: "Account"
    },
    {
      fieldname: "item_group",
      label: "Item Group",
      fieldtype: "Link",
      options: "Item Group"
    },
    {
      fieldname: "item_code",
      label: "Item",
      fieldtype: "Link",
      options: "Item"
    },
    {
      fieldname: "customer_group",
      label: "Customer Group",
      fieldtype: "Link",
      options: "Customer Group"
    },
    {
      fieldname: "customer",
      label: "Customer",
      fieldtype: "Link",
      options: "Customer"
    },
    {
      fieldname: "patient",
      label: "Patient",
      fieldtype: "Link",
      options: "Patient"
    },
    {
      fieldname: "doctor",
      label: "Doctor",
      fieldtype: "Link",
      options: "Healthcare Practitioner"
    },
    {
      fieldname: "show_unallocated_payment_entries",
      label: "Show Unallocated Payment Entries",
      fieldtype: "Check",
      default: 1
    }
  ],

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (data && data.status === "Unallocated") {
      value = `<span style="color:#d73502;font-weight:600">${value}</span>`;
    }

    if (column.fieldname === "discount_amount" && data && data.discount_amount > 0) {
      value = `<span style="font-weight:700">${value}</span>`;
    }

    if (data && data.is_total_row) {
      value = `<b>${value}</b>`;
    }

    return value;
  }
};
