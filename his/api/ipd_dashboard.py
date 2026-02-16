import  frappe
from erpnext.accounts.utils import get_balance_on
from frappe.utils import getdate
@frappe.whitelist()
def admit_dashboard():

	
	ip_r = frappe.db.sql(f""" select
	patient,  
	patient_name,
	room,
	bed,
	type from `tabInpatient Record` where status="Admitted" """ , as_dict = True)
	# totl_bills = frappe.db.sql(f""" 
	# 			select patient,patient_name,sum(net_total) as 'totl_bills' 
	# 			from `tabSales Invoice` where docstatus=1 group by patient
				

	#  """ , as_dict = True)
	# frappe.errprint(totl_bills)
	# credits1 = frappe.db.sql(f""" 
	# select 
	# `tabCustomer`.`customer_name`,
	# `tabCustomer Credit Limit`. `credit_limit`
	#  from `tabCustomer`
	# INNER JOIN `tabCustomer Credit Limit` ON `tabCustomer`.`name` = `tabCustomer Credit Limit`.`parent` group by customer_name

	#  """ , as_dict = True)
	# frappe.errprint(credits)
	# dict1 = {}
	# dict2 = {}

	for data in ip_r:
		# key = (data["patient"],data["patient_name"])
		# dict1[key] = data
		data["allowed_credit"] = frappe.db.get_value("Customer Credit Limit",{"parent":frappe.db.get_value("Patient",(data["patient"]),"customer")},"credit_limit")
		data["balance"]= get_balance_on(company = frappe.defaults.get_user_default("Company"),
						party_type ="Customer",
						party =frappe.db.get_value("Patient",(data["patient"]), "customer"),
						date = getdate())
		# if key in dict1:
		# 	dict1[key].update(data)
		# else:
		# 	dict1[key] = data

	# for data in totl_bills:
	# 	key = (data["patient"],data["patient_name"])
	# 	# dict2[key] = data
	# 	if key in dict1:
	# 		dict1[key].update(data)
			


	# Convert dict1 back to a list
	# patient_list = list(dict1.values())
		
	return ip_r

	# return ip_r
@frappe.whitelist()
def discharge_p_da():
	discharged = frappe.db.sql(f""" select
	patient,  
	patient_name,
	room,
	bed,
	clearance_status,
	type from `tabInpatient Record` where status="Discharge Scheduled" """ , as_dict = True)
	
	
	for data in discharged:
		data["allowed_credit"] = frappe.db.get_value("Customer Credit Limit",{"parent":frappe.db.get_value("Patient",(data["patient"]),"customer")},"credit_limit")
		data["balance"]= get_balance_on(company = frappe.defaults.get_user_default("Company"),
						party_type ="Customer",
						party =frappe.db.get_value("Patient",(data["patient"]), "customer"),
						date = getdate())
	
	return discharged

@frappe.whitelist()
def admission_ordered():
	admission = frappe.db.sql(f""" select
	patient,  
	patient_name,
	room,
	bed,
	status,
	type from `tabInpatient Record` where status="Admission Scheduled" """ , as_dict = True)
	
	
	for data in admission:
		data["allowed_credit"] = frappe.db.get_value("Customer Credit Limit",{"parent":frappe.db.get_value("Patient",(data["patient"]),"customer")},"credit_limit")
		data["balance"]= get_balance_on(company = frappe.defaults.get_user_default("Company"),
						party_type ="Customer",
						party =frappe.db.get_value("Patient",(data["patient"]), "customer"),
						date = getdate())
	return admission

@frappe.whitelist()
def doctor_plan():
	data = frappe.db.sql(f"""
		select

		`tabDoctor Plan`.`name`,`tabDoctor Plan`.`patient_name`,`tabDoctor Plan`.`ref_practitioner`,
		`tabIPD Drug Prescription`.`drug_code`,`tabIPD Drug Prescription`.`quantity`,`tabIPD Drug Prescription`.`used_qty`,`tabIPD Drug Prescription`.`ordered_qty`
		from `tabDoctor Plan`
		INNER JOIN `tabIPD Drug Prescription` ON `tabDoctor Plan`.`name` = `tabIPD Drug Prescription`.`parent`

		""" , as_dict = 1)
	return data 
@frappe.whitelist()
def bed_status():
    bed = frappe.db.sql(f""" 
        select
        
		
        SUM(if(occupancy_status = 'Vacant', 1, 0)) AS Vacant,
        SUM(if(occupancy_status = 'Occupied', 1, 0)) AS 'Occupied',
        SUM(if(occupancy_status = 'Discharge Ordered', 1, 0)) AS 'Discharge',
        SUM(if(occupancy_status = 'In Cleaning', 1, 0)) AS 'InCleaning',

        SUM(if(occupancy_status = 'Vacant', 1, 0)+if(occupancy_status = 'Occupied', 1, 0)+if(occupancy_status = 'Discharge Ordered', 1, 0)+if(occupancy_status = 'In Cleaning', 1, 0)) as Total
		from `tabHealthcare Service Unit`
     """ , as_dict = True)

    return bed  