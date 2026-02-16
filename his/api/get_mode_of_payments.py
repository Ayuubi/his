import frappe
from erpnext.stock.get_item_details import get_pos_profile
@frappe.whitelist()
def mode_of_payments(company = None) :
		company = frappe.defaults.get_user_default("company")
		pos_profile = get_pos_profile(company)
		mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
		default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
		return default_account, pos_profile.write_off_cost_center

