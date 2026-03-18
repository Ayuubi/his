// item_wise_sales_register_patient.js
frappe.query_reports["Item Wise Sales Register Patient"] = {
  filters: [
    { fieldname: "view", label: "View", fieldtype: "Select", options: "Detail\nSummary", default: "Detail", reqd: 1 },
    { fieldname: "group_by", label: "Group By", fieldtype: "Select", options: "Item\nItem Group\nCustomer\nPatient\nPractitioner\nInvoice\nPosting Date", default: "Item Group" },

    { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1, default: frappe.datetime.month_start() },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },

    { fieldname: "company", label: "Company", fieldtype: "Link", options: "Company" },

    { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" },
    { fieldname: "patient", label: "Patient", fieldtype: "Link", options: "Patient" },

    { fieldname: "ref_practitioner", label: "Ref Practitioner", fieldtype: "Link", options: "Healthcare Practitioner" },

    { fieldname: "item_code", label: "Item", fieldtype: "Link", options: "Item" },
    { fieldname: "item_group", label: "Item Group", fieldtype: "Link", options: "Item Group" },

	
	
    // NEW: Age range
    { fieldname: "age_from", label: "Age From", fieldtype: "Int" },
    { fieldname: "age_to", label: "Age To", fieldtype: "Int" },

	// NEW: Inpatient toggle (only affects invoices)
    { fieldname: "exclude_inpatient", label: "Exclude Inpatient Records", fieldtype: "Check", default: 1 },
  ],
};