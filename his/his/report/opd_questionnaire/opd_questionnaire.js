// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["OPD questionnaire"] = {
	filters: [
		{
		  fieldname: "from_date",
		  label: __("From Date"),
		  fieldtype: "Date",
		  default: frappe.datetime.now_date(),
		  reqd: 1,
		},
		{
		  fieldname: "to",
		  label: __("To Date"),
		  fieldtype:  "Date",
		  default: frappe.datetime.now_date(),
		  reqd: 1,
		},
		{
		 	fieldname: "department",
		 	label: __("Department"),
		 	fieldtype: "Select",
		 	"options": "Consulation\nE.R\nPharmacy\nMeternity\nLab and Collection"
	
		 },
	  ],
};
