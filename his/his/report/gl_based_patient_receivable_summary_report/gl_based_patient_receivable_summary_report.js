// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GL-based Patient Receivable Summary Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Shaafi Hospital"
		},
		{
			fieldname: "to_date",
			label: __("As Of Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "party_type",
			label: __("Ledger Party Type"),
			fieldtype: "Select",
			options: "Customer\nEmployee",
			default: "Customer",
			reqd: 1,
			description: __("Customer = patient / insurance / other customer ledgers. Employee = employee ledger balances.")
		},
		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "Data"
		},
		{
			fieldname: "patient",
			label: __("Patient"),
			fieldtype: "Link",
			options: "Patient"
		},
		{
			fieldname: "billing_category",
			label: __("Billing Category"),
			fieldtype: "Select",
			options: "\nPatient Ledger\nInsurance Ledger\nEmployee Ledger\nUnmapped Customer Ledger"
		},
		{
			fieldname: "receivable_state",
			label: __("Receivable State"),
			fieldtype: "Select",
			options: "\nOPD\nIPD Admitted\nIPD Discharged\nInsurance\nUnmapped Customer\nEmployee Ledger\nEmployee / OPD\nEmployee / IPD Admitted\nEmployee / IPD Discharged"
		},
		{
			fieldname: "only_with_discharge_balance",
			label: __("Only With Discharge Date"),
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "sort_by",
			label: __("Sort By"),
			fieldtype: "Select",
			options: "\ncurrent_ledger_balance\nbalance_at_discharge\npost_discharge_movement\nparty_name\npatient_name\nbilling_category\nreceivable_state",
			default: "current_ledger_balance"
		}
	]
};
