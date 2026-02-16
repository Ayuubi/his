frappe.query_reports["Doctor Sales By Item Group"] = {
  "filters": [
    {
      "fieldname": "from_date",
      "label": __("From Date"),
      "fieldtype": "Date",
      "default": frappe.datetime.add_days(frappe.datetime.get_today(), -30),
      "reqd": 1
    },
    {
      "fieldname": "to_date",
      "label": __("To Date"),
      "fieldtype": "Date",
      "default": frappe.datetime.get_today(),
      "reqd": 1
    },
    {
      "fieldname": "ref_practitioner",
      "label": __("Doctor"),
      "fieldtype": "Link",
      "options": "Healthcare Practitioner",
      // changed reqd to 0 to view all doctors requed by Eng Farah
      "reqd": 0
    },
    {
      "fieldname": "company",
      "label": __("Company"),
      "fieldtype": "Link",
      "options": "Company",
      "default": frappe.defaults.get_user_default("company")
    }
  ]
};
