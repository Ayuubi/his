from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
import frappe
class CustomSalesInvoice(SalesInvoice):


	def check_credit_limit(self):
		from erpnext.selling.doctype.customer.customer import check_credit_limit

		validate_against_credit_limit = False
		bypass_credit_limit_check_at_sales_order = frappe.db.get_value(
			"Customer Credit Limit",
			filters={"parent": self.customer, "parenttype": "Customer", "company": self.company},
			fieldname=["bypass_credit_limit_check"],
		)

		if bypass_credit_limit_check_at_sales_order:
			validate_against_credit_limit = True
		paid_amount = 0
		if self.payments:
			paid_amount = self.payments[0].amount 
		frappe.errprint(self.net_total)
		if not self.is_pos   and not self.is_free and not self.is_insurance:
			# frappe.msgprint("tan kore")
			validate_against_credit_limit = True
		if  float(paid_amount) < float(self.net_total)  and not self.is_free and not self.is_insurance:
			# frappe.msgprint("tan hoose")
			validate_against_credit_limit = True
	
		if validate_against_credit_limit:
			check_credit_limit(self.customer, self.company, bypass_credit_limit_check_at_sales_order)

