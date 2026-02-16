// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["IPD questionnaire"] = {
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
		 	"options": "How often did nurses treat you with courtesy and respect?\nHow often did nurses explain things in a way you could understand?\nHow often did nurses listen carefully to you?\nTimely medication & care:\nResponse of staff to your Concerns or Complaints"
	
		 },
	  ],
};
