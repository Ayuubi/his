# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import timedelta , date
from frappe.utils import getdate


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)[0]
	return columns, data

def get_data(filters):
	cash_bank_acc = ('Cash' , 'Bank')
	cash_accounts =  frappe.db.sql_list(f""" select name from tabAccount  where account_type in {cash_bank_acc} and is_group = 0 and root_type = "Asset" """)
	daily_cash = []
	account_names = []
	for date in daterange(getdate(filters.from_date) , getdate(filters.to_date)):
		daily = {}
		total = 0
		for acc in cash_accounts:
			
			report_gl = frappe.get_doc("Report", "General Ledger")

			report_gl_filters = {
					"company" :frappe.defaults.get_user_default("company"),
			
					"from_date": frappe.utils.getdate(date),
					"to_date": frappe.utils.getdate(date),
					"account" : [acc]
			
				}
			
			columns_gl, data_gl = report_gl.get_data(
						limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
					)
			if data_gl[-2].balance != 0:
				total += data_gl[-2].balance

				daily['date'] = date
				daily[frappe.scrub(acc)] = data_gl[-2].balance
				daily['total'] = total
				
				
				account_names.append(acc)

		daily_cash.append(daily)
	return daily_cash , account_names





def daterange(start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)

def get_columns(filters):
	columns = [
			{
				"label": "Date",
				"fieldname": "date",
				"fieldtype": "Date",
				
				"width": 120,
			}
	]
	cash_bank_acc = ('Cash' , 'Bank')
	income_accounts = frappe.db.sql_list(f""" select name from tabAccount where account_type in {cash_bank_acc} and is_group = 0 """)

	report_cols = get_data(filters)[1]

	for account in income_accounts:
		if account in  report_cols:
			columns.append(
					{
						"label": account,
						"fieldname": frappe.scrub(account),
						"fieldtype": "Currency",
						
						"width": 220,
					}
				)
	columns.append(
		{
					"label": "Total",
					"fieldname": "total",
					"fieldtype": "Currency",
					
					"width": 100,
				}
	)
	return columns