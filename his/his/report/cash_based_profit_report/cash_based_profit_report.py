# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


# ======================
# COLUMNS
# ======================
def get_columns(filters):

	if filters.get("show_details"):
		return [
			{"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 180},
			{"label": "Voucher", "fieldname": "voucher", "fieldtype": "Data", "width": 180},
			{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
			{"label": "Party", "fieldname": "party", "fieldtype": "Data", "width": 200},
			{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
		]

	return [
		{
			"label": "Description",
			"fieldname": "description",
			"fieldtype": "Data",
			"width": 250
		},
		{
			"label": "Amount",
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 180
		}
	]


# ======================
# DATA
# ======================
def get_data(filters):

	if filters.get("show_details"):
		return get_detailed_data(filters)

	revenue = get_cash_revenue(filters)
	expenses = get_expenses(filters)
	net = revenue - expenses

	return [
		{"description": "Cash Revenue", "amount": revenue},
		{"description": "Expenses", "amount": expenses},
		{"description": "Net Profit", "amount": net},
	]


# ======================
# SUMMARY REVENUE
# ======================
def get_cash_revenue(filters):

	sales = frappe.db.sql("""
		SELECT COALESCE(SUM(paid_amount), 0)
		FROM `tabSales Invoice`
		WHERE docstatus = 1
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", filters)[0][0] or 0

	receipts = frappe.db.sql("""
		SELECT COALESCE(SUM(paid_amount), 0)
		FROM `tabPayment Entry`
		WHERE docstatus = 1
		AND payment_type = 'Receive'
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", filters)[0][0] or 0

	return sales + receipts


# ======================
# EXPENSES
# ======================
def get_expenses(filters):

	expenses = frappe.db.sql("""
		SELECT COALESCE(SUM(gle.debit), 0)
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.docstatus = 1
		AND acc.root_type = 'Expense'
		AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", filters)[0][0] or 0

	return expenses


# ======================
# DETAIL VIEW
# ======================
def get_detailed_data(filters):

	data = []

	# Sales Invoice
	sales = frappe.db.sql("""
		SELECT
			'Sales Invoice' AS type,
			name AS voucher,
			posting_date AS date,
			customer AS party,
			paid_amount AS amount
		FROM `tabSales Invoice`
		WHERE docstatus = 1
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", filters, as_dict=1)

	data.append({"type": "=== SALES INVOICE ===", "voucher": "", "date": "", "party": "", "amount": ""})
	data += sales

	# Payment Entry
	payments = frappe.db.sql("""
		SELECT
			'Payment Entry' AS type,
			name AS voucher,
			posting_date AS date,
			party AS party,
			paid_amount AS amount
		FROM `tabPayment Entry`
		WHERE docstatus = 1
		AND payment_type = 'Receive'
		AND posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", filters, as_dict=1)

	data.append({"type": "=== PAYMENT ENTRY ===", "voucher": "", "date": "", "party": "", "amount": ""})
	data += payments

	return data