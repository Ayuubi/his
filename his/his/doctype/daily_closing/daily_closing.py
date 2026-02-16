# Copyright (c) 2024, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.get_mode_of_payments import mode_of_payments
from erpnext.stock.get_item_details import get_pos_profile
from erpnext.accounts.utils import get_balance_on
from frappe.utils import getdate

class DailyClosing(Document):
	pass

# get_balance_on(company = frappe.defaults.get_user_default("Company"),
# 						party_type ="Customer",
# 						party = customer,
# 						date = getdate())

@frappe.whitelist()
def get_balance():
	pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	account= frappe.get_doc("Mode of Payment", mode_of_payment)
	acc= account.accounts[0].default_account
	acc_balance=0
	if acc:
		acc_balance = get_balance_on(acc, date=getdate())
		
	return acc_balance, acc
@frappe.whitelist()
def get_comm():
	data = frappe.db.sql(f"""
		SELECT
			sum(commission) as comm
			FROM `tabSales Invoice` 
				
			WHERE docstatus= 1 and owner = '{frappe.session.user}' and posting_date= '{getdate()}'
		""",  as_dict=1)
	# frappe.errprint(data)
	return data[0].comm
