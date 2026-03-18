// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Patient Receivable Summary Report"] = {
	filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "to_date",
            label: __("As Of Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "patient",
            label: __("Patient"),
            fieldtype: "Link",
            options: "Patient"
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "billing_source",
            label: __("Billing Source"),
            fieldtype: "Select",
            options: "\nPatient\nInsurance\nPatient Transfer\nEmployee"
        },
        {
            fieldname: "receivable_state",
            label: __("Receivable State"),
            fieldtype: "Select",
            options: "\nOPD\nIPD Admitted\nIPD Discharged\nMixed\nOPD / Reconciliation Issue\nIPD Admitted / Reconciliation Issue\nIPD Discharged / Reconciliation Issue\nMixed / Reconciliation Issue\nUnclassified Ledger Balance"
        },
        {
            fieldname: "min_outstanding",
            label: __("Min Outstanding"),
            fieldtype: "Currency"
        },
        {
            fieldname: "only_with_difference",
            label: __("Only With Difference"),
            fieldtype: "Check",
            default: 0
        },
        {
            fieldname: "sort_by",
            label: __("Sort By"),
            fieldtype: "Select",
            options: "\nclassified_invoice_total\nledger_receivable_balance\ndifference\nopd_invoice_outstanding\nipd_admitted_invoice_outstanding\nipd_discharged_invoice_outstanding\npatient_name\nbilling_source",
            default: "classified_invoice_total"
        }
    ]
};
