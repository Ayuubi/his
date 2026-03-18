// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Loyalty Program Eligibility"] = {
  filters: [
    {
      fieldname: "patient",
      label: "Patient",
      fieldtype: "Link",
      options: "Patient",
    },
    {
      fieldname: "customer",
      label: "Customer",
      fieldtype: "Link",
      options: "Customer",
    },
    { fieldname: "from_date", label: "From Date", fieldtype: "Date" },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date" },

    { fieldname: "days_window", label: "Days Window", fieldtype: "Int", default: 180 },

    { fieldname: "points_per_visit", label: "Points per Visit", fieldtype: "Int", default: 2 },
    { fieldname: "min_visit_days", label: "Minimum Visit Days", fieldtype: "Int", default: 25 },
    { fieldname: "min_spending", label: "Minimum Spending", fieldtype: "Currency", default: 2000 },

    {
      fieldname: "eligibility_mode",
      label: "Eligibility Mode",
      fieldtype: "Select",
      options: "OR\nAND",
      default: "OR",
      description: "OR = eligible if Visits OR Spending passes",
    },

    { fieldname: "only_submitted", label: "Only Submitted (docstatus=1)", fieldtype: "Check", default: 1 },
    { fieldname: "company", label: "Company", fieldtype: "Link", options: "Company" },
  ],
};