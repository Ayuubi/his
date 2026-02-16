# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from his.api.get_mode_of_payments import mode_of_payments 
from frappe.utils import getdate
class Dailycasheircashclosing(Document):
	# pass
	def on_submit(self):
		pass
	@frappe.whitelist()
	def get_cashier_score(self , date):

		company = frappe.defaults.get_user_default("company")
		report_gl = frappe.get_doc("Report", "General Ledger")


		
		report_gl_filters = {
			
			"company": company,
			"account" : [mode_of_payments()[0]],
			"from_date": getdate(date),
			"to_date": getdate(date),
			"group_by": "Group by Voucher (Consolidated)",
		}
		# if  account:
		

		# frappe.errprint(report_gl_filters)
		columns_gl, data_gl = report_gl.get_data(
			user="Administrator", filters=report_gl_filters, as_dict=True
		)
		closing_data = {}
		closing ={}
		closing_data_list = []
		for d in data_gl:
			if d.voucher_type:
				vo_typ_debit = d.voucher_type.lower().replace(' ','_')+"_debit"
				vo_typ_credit = d.voucher_type.lower().replace(' ','_')+"_credit"
				# frappe.msgprint(str(vo_typ_debit))
				if vo_typ_debit in  closing_data:
					closing_data[vo_typ_debit] += d.debit
				else:
					closing_data[vo_typ_debit] = d.debit

				if vo_typ_credit in closing_data:
					closing_data[vo_typ_credit] += d.credit
				else:
					closing_data[vo_typ_credit] = d.credit
			
		if 'sales_invoice_debit' in closing_data  and 'sales_invoice_credit' in closing_data:
			closing['cash_sales'] = closing_data['sales_invoice_debit'] - closing_data['sales_invoice_credit']
		if  'payment_entry_debit' in closing_data:
			closing['reciept'] = closing_data['payment_entry_debit']
		if 'payment_entry_credit' in closing_data:
			closing['payment'] = closing_data['payment_entry_credit']
		if 'journal_entry_debit' in closing_data:
			closing['other_income'] = closing_data['journal_entry_debit']
		if 'journal_entry_credit' in  closing_data:
			closing['expense'] = closing_data['journal_entry_credit']
		
		# closing_data
		
		return [closing]



	def on_submit(self):
		doc=self
		
		company = frappe.defaults.get_global_default("company")
		abbr = frappe.get_value("Company", company, "abbr")
		# dat=self.posting_date


		Journal = frappe.get_doc({
					"doctype" : "Journal Entry",
					"posting_date": frappe.utils.getdate(),
					"accounts": [{
					"account": "Main Cashier - "+abbr,
					
					"debit_in_account_currency": doc.cash_in_hand,
					"doctype": "Journal Entry Account"
				
				
						},
						
						{
					"account": doc.account,
					"credit_in_account_currency": doc.cash_in_hand,
					# "source_order" : "Cashiers Closing",
					"doctype": "Journal Entry Account"
				
				
						}]
				
					})
		Journal.insert()
		Journal.submit()
					#frappe.db.sql(f""" update  `tabDaily casheir cash closing` set status='Approved' where owner='{user}' and posting_date='{dat}'; """ ,as_dict=True )
		doc.status="Aproved!"	
		
		frappe.msgprint("Transfered Successfully!!")
				