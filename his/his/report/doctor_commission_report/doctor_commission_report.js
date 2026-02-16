// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */



frappe.query_reports["Doctor Commission Report"] = {
  filters: [
    { fieldname:"from_date", label:__("From Date"), fieldtype:"Date", default:frappe.datetime.get_today(), reqd:1 },
    { fieldname:"to_date", label:__("To Date"), fieldtype:"Date", default:frappe.datetime.get_today(), reqd:1 },
    { fieldname:"practitioner", label:__("Doctor"), fieldtype:"Link", options:"Healthcare Practitioner" },
	{ fieldname:"item_group", label:__("Item Group"), fieldtype:"Link", options:"Item Group" },
    { fieldname:"source_order", label:__("Source Order"), fieldtype:"Link", options:"Source Order" }
  ]
};
