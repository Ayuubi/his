# Copyright (c) 2024, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.get_mode_of_payments import mode_of_payments
from erpnext.stock.get_item_details import get_pos_profile
from erpnext.accounts.utils import get_balance_on
from frappe.model.document import Document

class EmployeeReceipt(Document):
	pass
@frappe.whitelist()
def get_account():
	pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	account= frappe.get_doc("Mode of Payment", mode_of_payment)
	acc= account.accounts[0].default_account

		
	return  acc