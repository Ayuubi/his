# Copyright (c) 2015, Frappe Technologies Pvt. Ltd.
# Optimized variant by consolidating queries & fixing minor bugs.

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
	return AccountReceivableSummary(filters).run(args)


class AccountReceivableSummary(ReceivablePayableReport):
	def run(self, args):
		self.party_type = args.get("party_type")
		self.party_naming_by = frappe.db.get_value(
			args.get("naming_by")[0], None, args.get("naming_by")[1]
		)
		self.get_columns()
		self.get_data(args)
		return self.columns, self.data

	def get_data(self, args):
		self.data = []

		# base receivables
		self.receivables = ReceivablePayableReport(self.filters).run(args)[1]
		self.get_party_total(args)

		parties = list(self.party_total.keys())
		if not parties:
			return

		report_date = self.filters.report_date
		company = self.filters.company

		# --- batch fetches (avoid N+1) ---------------------------------------
		# 1) map: party -> customer_name
		customer_rows = frappe.db.get_all(
			"Customer",
			filters={"name": ("in", parties)},
			fields=["name", "customer_name"],
			pluck=None,
		)
		customer_name_map = {r.name: r.customer_name for r in customer_rows}

		# # 2) inpatient info for only those customer_names we care about
		# customer_names = list({cn for cn in customer_name_map.values() if cn})
		# inpatient_rows = []
		# if customer_names:
		# 	inpatient_rows = frappe.db.get_all(
		# 		"Inpatient Record",
		# 		filters={"patient_name": ("in", customer_names), "status": ["in", ["Discharge Scheduled", "Admitted", "Discharged"]],},
		# 		fields=["patient_name", "room", "bed", "patient"],
		# 	)
		# # map: patient_name -> inpatient record fields
		# inpatient_map = {r.patient_name: r for r in inpatient_rows}

		# 2) inpatient info for only those customer_names we care about
		customer_names = list({cn for cn in customer_name_map.values() if cn})

		# Status filter (supports MultiSelectList -> list OR comma-separated string)
		default_statuses = ["Discharge Scheduled", "Admitted" ] #, "Discharged"]
		statuses = self.filters.get("inpatient_status") or default_statuses

		# if someone passes "Admitted,Discharged" as string
		if isinstance(statuses, str):
			statuses = [s.strip() for s in statuses.split(",") if s.strip()]

		inpatient_rows = []
		if customer_names:
			inpatient_rows = frappe.db.get_all(
				"Inpatient Record",
				filters={
					"patient_name": ("in", customer_names),
					"status": ("in", statuses),
				},
				fields=["patient_name", "room", "bed", "patient", "status"],
			)

		# map: patient_name -> inpatient record fields
		# NOTE: if there can be multiple inpatient records per patient_name,
		# you may want "latest" logic. For now this keeps the last row returned.
		inpatient_map = {r.patient_name: r for r in inpatient_rows}


		# 3) credit limits in bulk
		credit_rows = frappe.db.get_all(
			"Customer Credit Limit",
			filters={"parent": ("in", parties)},
			fields=["parent", "credit_limit"],
		)
		credit_map = {}
		for r in credit_rows:
			# if multiple rows per parent exist, you could aggregate or pick first
			credit_map.setdefault(r.parent, r.credit_limit)

	# 4) contacts (your original code used Contact named as f"{party}-{party}")
		
		# 5) party advance amounts (kept, though unused in original output)
		party_advance_amount = get_partywise_advanced_payment_amount(
			self.party_type,
			report_date,
			self.filters.show_future_payments,
			company,
		) or {}

		# 6) optional GL balance map
		gl_balance_map = {}
		if self.filters.show_gl_balance:
			gl_balance_map = get_gl_balance(report_date)
		# ----------------------------------------------------------------------

		# build rows
		for party, party_dict in iteritems(self.party_total):
			# skip zero outstanding
			# if flt(party_dict.outstanding) == 0:
			# 	continue
			if abs(flt(party_dict.outstanding, 2)) == 0:
				continue

			# only include if this party's customer_name is an inpatient
			customer_name = customer_name_map.get(party)
			if not customer_name:
				continue

			ip = inpatient_map.get(customer_name)
			if not ip:
				continue  # customer is not currently inpatients; skip

			row = frappe._dict()
			row.party = party

			# "Naming Series" means show the *_name field
			if self.party_naming_by == "Naming Series":
				row.party_name = frappe.get_cached_value(
					self.party_type, party, scrub(self.party_type) + "_name"
				)

			# inpatient fields
			row.room = ip.room
			row.bed = ip.bed
			row.patient = ip.patient
			row.patient_name = ip.patient_name
			row.inpatient_status = ip.status


			# credit & contact (best-effort)
			row.credit_limit = credit_map.get(party)

			# money fields from the aggregated party_dict
			row.update(party_dict)

			# if you want to reflect advances separately, uncomment:
			# row.advance = flt(party_advance_amount.get(party, 0))
			# row.paid = flt(row.paid) + row.advance

			# action buttons (keep HTML compact & safe)
			outstanding = flt(party_dict.outstanding)
			outstanding_with_5pct = flt(outstanding * 1.05)
			row.receipt = (
				f"<button style='padding:3px;margin:-5px' class='btn btn-primary' "
				f"onClick='receipt(\"{frappe.utils.escape_html(party)}\", "
				f"\"{outstanding}\", \"{outstanding_with_5pct}\")'>Receipt</button>"
			)
			row.statement = (
				f"<button style='padding:3px;margin:-5px' class='btn btn-primary' "
				f"onClick='statement(\"{frappe.utils.escape_html(party)}\")'>Statements</button>"
			)

			if self.filters.show_gl_balance:
				row.gl_balance = flt(gl_balance_map.get(party))
				row.diff = flt(row.outstanding) - flt(row.gl_balance)

			self.data.append(row)

	def get_party_total(self, args):
		self.party_total = frappe._dict()
		for d in self.receivables:
			self.init_party_total(d)
			# Add all amount columns present on row d
			for k in list(self.party_total[d.party]):
				if k not in ["currency", "sales_person"]:
					self.party_total[d.party][k] += d.get(k, 0.0)
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
					"range1": 0.0,
					"range2": 0.0,
					"range3": 0.0,
					"range4": 0.0,
					"range5": 0.0,
					"total_due": 0.0,
					"sales_person": [],
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

	def get_columns(self):
		self.columns = []
		self.add_column(
			label=_(self.party_type),
			fieldname="party",
			fieldtype="Link",
			options=self.party_type,
			width=180,
		)
		

		self.add_column(_("Patient"), fieldname="patient", width=100, fieldtype="Data")
		self.add_column(_("Patient Name"), fieldname="patient_name", width=300, fieldtype="Data")
		if self.party_naming_by == "Naming Series":
			self.add_column(_("{0} Name").format(self.party_type), fieldname="party_name", width=200, fieldtype="Data")
		self.add_column(_("Room"), fieldname="room", width=200, fieldtype="Data")
		self.add_column(_("Bed"), fieldname="bed", width=200, fieldtype="Data")
		self.add_column(_("IP Status"), fieldname="inpatient_status", width=140, fieldtype="Data")
		# self.add_column(_("Mobile No"), fieldname="mobile_no", fieldtype="Data")

		credit_debit_label = "Return" if self.party_type == "Customer" else "Debit Note"
		# self.add_column(_("Advance Amount"), fieldname="advance")
		# self.add_column(_("Invoiced Amount"), fieldname="invoiced")
		# self.add_column(_("Paid Amount"), fieldname="paid")
		# self.add_column(_(credit_debit_label), fieldname="credit_note")

		self.add_column(_("Balance"), fieldname="outstanding")
		self.add_column(_("Receipt"), fieldname="receipt", fieldtype="Data")
		self.add_column(_("Print Statement"), fieldname="statement", fieldtype="Data")

		if self.filters.show_gl_balance:
			self.add_column(_("GL Balance"), fieldname="gl_balance")
			self.add_column(_("Difference"), fieldname="diff")

		if self.party_type == "Customer":
			if self.filters.show_sales_person:
				self.add_column(label=_("Sales Person"), fieldname="sales_person", fieldtype="Data")
		else:
			self.add_column(
				label=_("Supplier Group"),
				fieldname="supplier_group",
				fieldtype="Link",
				options="Supplier Group",
			)

	def setup_ageing_columns(self):
		for i, label in enumerate(
			[
				"0-{range1}".format(range1=self.filters["range1"]),
				"{range1}-{range2}".format(range1=cint(self.filters["range1"]) + 1, range2=self.filters["range2"]),
				"{range2}-{range3}".format(range2=cint(self.filters["range2"]) + 1, range3=self.filters["range3"]),
				"{range3}-{range4}".format(range3=cint(self.filters["range3"]) + 1, range4=self.filters["range4"]),
				"{range4}-{above}".format(range4=cint(self.filters["range4"]) + 1, above=_("Above")),
			]
		):
			self.add_column(label=label, fieldname="range" + str(i + 1))
		self.add_column(label="Total Amount Due", fieldname="total_due")


def get_gl_balance(report_date):
	return frappe._dict(
		frappe.db.get_all(
			"GL Entry",
			fields=["party", "sum(debit - credit)"],
			filters={"posting_date": ("<=", report_date), "is_cancelled": 0},
			group_by="party",
			as_list=1,
		)
	)
