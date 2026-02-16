import frappe
@frappe.whitelist()
def get_patient_pro(empl):

	 que=frappe.db.sql(f""" select count(*) as que from `tabQue` where patient_name="{empl}" and date=CURRENT_DATE();  """ , as_dict=True)
	 doctor=frappe.db.sql(f""" select count(*) as doctor from `tabPatient Encounter` where patient_name="{empl}" and encounter_date=CURRENT_DATE();  """ , as_dict=True)
	 Cashier=frappe.db.sql(f""" select count(*) as cashier from `tabSales Order` where so_type="Cashiers" and patient_name="{empl}" and transaction_date=CURRENT_DATE();  """ , as_dict=True)
	 invoice=frappe.db.sql(f""" select count(*) as invoice from `tabSales Invoice` where source_order !="Que" and patient_name="{empl}" and posting_date=CURRENT_DATE();  """ , as_dict=True)
	 pharmacy=frappe.db.sql(f""" select count(*) as pharmacy from `tabSales Order` where so_type="Pharmacy" and patient_name="{empl}" and transaction_date=CURRENT_DATE();  """ , as_dict=True)
	 imaging=frappe.db.sql(f""" select count(*) as imaging from `tabRadiology` where patient_name="{empl}" and date=CURRENT_DATE();  """ , as_dict=True)
	 lab=frappe.db.sql(f""" select count(*) as lab from `tabLab Result` where patient_name="{empl}" and date=CURRENT_DATE();  """ , as_dict=True)

	 return que+doctor+Cashier+invoice+pharmacy+imaging+lab





	  
