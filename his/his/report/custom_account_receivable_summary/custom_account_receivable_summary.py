# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _, scrub
from frappe.utils import cint, flt
from six import iteritems
from erpnext.accounts.party import get_partywise_advanced_payment_amount
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	return AccountsReceivableSummary(filters).run(args)


class AccountsReceivableSummary(ReceivablePayableReport):
	def run(self, args):
		self.party_type = args.get("party_type")
		self.party_naming_by = frappe.db.get_value(
			args.get("naming_by")[0], None, args.get("naming_by")[1]
		)
		self.get_columns()
		self.get_data(args)
		return self.columns, self.data

	# def get_data(self, args):
	# 	self.data = []
	# 	self.receivables = ReceivablePayableReport(self.filters).run(args)[1]

	# 	self.get_party_total(args)
		

	# 	party_advance_amount = (
	# 		get_partywise_advanced_payment_amount(
	# 			self.party_type,
	# 			self.filters.report_date,
	# 			self.filters.show_future_payments,
	# 			self.filters.company,
	# 			party=self.filters.get(scrub(self.party_type)),
	# 		)
	# 		or {}
	# 	)

	# 	if self.filters.show_gl_balance:
	# 		gl_balance_map = get_gl_balance(self.filters.report_date)

	# 	for party, party_dict in self.party_total.items():
	# 		if round(party_dict.outstanding, 10) == 0:
	# 			continue

	# 		row = frappe._dict()

	# 		row.party = party
	# 		if self.party_naming_by == "Naming Series":
	# 			row.party_name = frappe.get_cached_value(
	# 				self.party_type, party, scrub(self.party_type) + "_name"
	# 			)
	# 		row.patient =frappe.db.get_value("Patient",{"customer" : party},"name")
	# 		row.resonsible =frappe.db.get_value("Customer Credit Limit",{"parent":party},"responsible")
	# 		row.mobile_no = frappe.db.get_value("Patient",{"customer" : party},"mobile_no")
	# 		# row.status = frappe.db.get_value("Inpatient Record", {"patient": frappe.db.get_value("Patient",{"customer" : party},"name")}, "status")
	# 		row.receipt	  =f"""<button style='padding: 3px; margin:-5px' class= 'btn btn-primary' onClick='receipt("{party}" , "{party_dict.outstanding}" , "{party_dict.outstanding * 1.05}")'>Receipt</button>"""
	# 		row.statement =f"""<button style='padding: 3px; margin:-5px' class= 'btn btn-primary' onClick='statement("{party}")'>Statements</button>"""

	# 		row.update(party_dict)

	# 		# Advance against party
	# 		row.advance = party_advance_amount.get(party, 0)

	# 		# In AR/AP, advance shown in paid columns,
	# 		# but in summary report advance shown in separate column
	# 		row.paid -= row.advance

	# 		if self.filters.show_gl_balance:
	# 			row.gl_balance = gl_balance_map.get(party)
	# 			row.diff = flt(row.outstanding) - flt(row.gl_balance)

	# 		if self.filters.show_future_payments:
	# 			row.remaining_balance = flt(row.outstanding) - flt(row.future_amount)

	# 		self.data.append(row)


	def get_data(self, args):
		self.data = []

		# Run base report logic
		self.receivables = ReceivablePayableReport(self.filters).run(args)[1]

		self.get_party_total(args)

		# 🔄 Batch fetch responsible persons
		responsible_map = frappe._dict({
			r.parent: r.responsible
			for r in frappe.get_all("Customer Credit Limit", fields=["parent", "responsible"])
		})

		# 🔄 Batch fetch mobile numbers
		patient_info_map = frappe._dict({
			r.customer: {"mobile_no": r.mobile_no, "name": r.name}
			for r in frappe.get_all("Patient", fields=["customer", "mobile_no", "name"])
		})

		# 🔄 Batch fetch status from Inpatient Record using patient names
		patient_names = [info["name"] for info in patient_info_map.values() if info.get("name")]
		# status_map = frappe._dict({
		# 	r.patient: r.status
		# 	for r in frappe.get_all("Inpatient Record", filters={"patient": ["in", patient_names]}, fields=["patient", "status"])
		# })

		# 🔄 Optional: batch fetch customer names if using naming series
		if self.party_naming_by == "Naming Series":
			party_name_map = frappe._dict({
				r.name: r.customer_name
				for r in frappe.get_all("Customer", fields=["name", "customer_name"])
			})

		# ✅ Advanced payments


		# ✅ GL balance map
		if self.filters.show_gl_balance:
			gl_balance_map = get_gl_balance(self.filters.report_date)

		for party, party_dict in iteritems(self.party_total):
			if round(party_dict.outstanding, 10) == 0:
				continue

			row = frappe._dict()
			row.party = party

			# ✅ Faster: use pre-fetched customer name
			if self.party_naming_by == "Naming Series":
				row.party_name = party_name_map.get(party)

			# ✅ Use batched values
			row.resonsible = responsible_map.get(party)
			# row.mobile_no = patient_info_map.get(party)
			row.mobile_no = patient_info_map.get(party, {}).get("mobile_no")
			row.patient = patient_info_map.get(party, {}).get("name")
			# row.status = status_map.get(row.patient)

			# Inline buttons
			row.receipt	  =f"""<button style='padding: 3px; margin:-5px' class= 'btn btn-primary' onClick='receipt("{party}" , "{party_dict.outstanding}" , "{party_dict.outstanding * 1.05}")'>Receipt</button>"""
			row.statement =f"""<button style='padding: 3px; margin:-5px' class= 'btn btn-primary' onClick='statement("{party}")'>Statements</button>"""

			row.update(party_dict)
			
			_ = row.paid  # dummy read

			if self.filters.show_gl_balance:
				row.gl_balance = gl_balance_map.get(party)
				row.diff = flt(row.outstanding) - flt(row.gl_balance)

			self.data.append(row)

	def get_party_total(self, args):
		self.party_total = frappe._dict()

		for d in self.receivables:
			self.init_party_total(d)

			# Add all amount columns
			for k in list(self.party_total[d.party]):
				if k not in ["currency", "sales_person"]:

					self.party_total[d.party][k] += d.get(k, 0.0)

			# set territory, customer_group, sales person etc
			self.set_party_details(d)

	def init_party_total(self, row):
		self.party_total.setdefault(
			row.party,
			frappe._dict(
				{
					"invoiced": 0.0,
					"paid": 0.0,
					"credit_note": 0.0,
					"outstanding": 0.0,
				
				}
			),
		)

	def set_party_details(self, row):
		self.party_total[row.party].currency = row.currency

		for key in ("territory", "customer_group", "supplier_group"):
			if row.get(key):
				self.party_total[row.party][key] = row.get(key)

		if row.sales_person:
			self.party_total[row.party].sales_person.append(row.sales_person)

		if self.filters.sales_partner:
			self.party_total[row.party]["default_sales_partner"] = row.get("default_sales_partner")

	def get_columns(self):
		self.columns = []
		
		self.add_column(
			label=_(self.party_type),
			fieldname="party",
			fieldtype="Link",
			options=self.party_type,
			width=180,
		)
		
		if self.party_naming_by == "Naming Series":
			self.add_column(_("{0} Name").format(self.party_type),
				   width=300,
				    fieldname="party_name", fieldtype="Data")
		self.add_column(_("Patient ID"), fieldname="patient", fieldtype="Data")
		self.add_column(_("Mobile No"), fieldname="mobile_no", fieldtype="Data")
		# self.add_column(_("Status"), fieldname="status", fieldtype="Data")
		self.add_column(_("Responsible"), fieldname="resonsible", fieldtype="Data")
		
		self.add_column(_("Balance"), fieldname="outstanding")
		self.add_column(_("Receipt"), fieldname="receipt" , fieldtype="Data")
		self.add_column(_("Print Statement"), fieldname="statement" , fieldtype="Data")
		

		if self.filters.show_gl_balance:
			self.add_column(_("GL Balance"), fieldname="gl_balance")
			self.add_column(_("Difference"), fieldname="diff")

		# self.setup_ageing_columns()

		if self.filters.show_future_payments:
			self.add_column(label=_("Future Payment Amount"), fieldname="future_amount")
			self.add_column(label=_("Remaining Balance"), fieldname="remaining_balance")



	def setup_ageing_columns(self):
		for i, label in enumerate(
			[
				"0-{range1}".format(range1=self.filters["range1"]),
				"{range1}-{range2}".format(
					range1=cint(self.filters["range1"]) + 1, range2=self.filters["range2"]
				),
				"{range2}-{range3}".format(
					range2=cint(self.filters["range2"]) + 1, range3=self.filters["range3"]
				),
				"{range3}-{range4}".format(
					range3=cint(self.filters["range3"]) + 1, range4=self.filters["range4"]
				),
				"{range4}-{above}".format(range4=cint(self.filters["range4"]) + 1, above=_("Above")),
			]
		):
			self.add_column(label=label, fieldname="range" + str(i + 1))

		# Add column for total due amount
		self.add_column(label="Total Amount Due", fieldname="total_due")


def get_gl_balance(report_date):
	return frappe._dict(
		frappe.db.get_all(
			"GL Entry",
			fields=["party", "sum(debit -  credit)"],
			filters={"posting_date": ("<=", report_date), "is_cancelled": 0},
			group_by="party",
			as_list=1,
		)
	)