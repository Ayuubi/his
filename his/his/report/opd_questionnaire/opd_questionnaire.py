# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt


from asyncio import Condition
import frappe

def execute(filters=None):
	columns, data =  get_columns(), get_data(filters)
	return columns, data

def get_data(filters):
	data =''
	cond=''
	_from, to = filters.get('from_date'), filters.get('to')
	if  filters.department=="Consulation":

	#     cond= ""
	# else:
	#      cond= f"and practitioner= '{filters.doctor}' "  
		data = frappe.db.sql(f"""
				select 
				SUBSTRING(creation, 1, 19) AS date,
				SUM(if(very_good = '1', 1, 0)) AS "very_good",    
				SUM(if(good = '1', 1, 0)) AS "good",
				SUM(if(fair = '1', 1, 0)) AS "fair",
				SUM(if(poor = '1', 1, 0)) AS "poor",
				SUM(if(very_poor = '1', 1, 0)) AS "very_poor"   
				from  `tabOut-patient questionnaire` 

			WHERE creation BETWEEN "{_from}" AND "{to}" 
		
			;""", as_dict=1)
	elif filters.department=="Pharmacy":
			data = frappe.db.sql(f"""
				select 
				SUBSTRING(creation, 1, 19) AS date,
				SUM(if(very_good_pharma = '1', 1, 0)) AS "very_good",    
				SUM(if(good_pharma = '1', 1, 0)) AS "good",
				SUM(if(fair_pharma = '1', 1, 0)) AS "fair",
				SUM(if(poor_pharma = '1', 1, 0)) AS "poor",
				SUM(if(very_poor_pharma = '1', 1, 0)) AS "very_poor"   
				from  `tabOut-patient questionnaire` 

				WHERE creation BETWEEN "{_from}" AND "{to}" 
		
			;""", as_dict=1)
	elif filters.department=="Lab and Collection":
		data = frappe.db.sql(f"""
			select 
			SUBSTRING(creation, 1, 19) AS date,
			SUM(if(very_good_blood_collection = '1', 1, 0)) AS "very_good",    
			SUM(if(good_blood_collection = '1', 1, 0)) AS "good",
			SUM(if(fair_blood_collection = '1', 1, 0)) AS "fair",
			SUM(if(poor_blood_collection = '1', 1, 0)) AS "poor",
			SUM(if(very_poor_blood_collection = '1', 1, 0)) AS "very_poor"   
			from  `tabOut-patient questionnaire` 

			WHERE creation BETWEEN "{_from}" AND "{to}" 
	
		;""", as_dict=1)
	elif filters.department=="E.R":
		data = frappe.db.sql(f"""
			select 
			SUBSTRING(creation, 1, 19) AS date,
			SUM(if(very_good_er = '1', 1, 0)) AS "very_good",    
			SUM(if(good_er = '1', 1, 0)) AS "good",
			SUM(if(fair_er = '1', 1, 0)) AS "fair",
			SUM(if(poor_er = '1', 1, 0)) AS "poor",
			SUM(if(very_poor_er = '1', 1, 0)) AS "very_poor"   
			from  `tabOut-patient questionnaire` 

			WHERE creation BETWEEN "{_from}" AND "{to}" 
		
			;""", as_dict=1)
	elif filters.department=="Meternity":
		data = frappe.db.sql(f"""
			select 
			SUBSTRING(creation, 1, 19) AS date,
			SUM(if(very_good_maternity_department = '1', 1, 0)) AS "very_good",    
			SUM(if(good_maternity_department = '1', 1, 0)) AS "good",
			SUM(if(fair_maternity_department = '1', 1, 0)) AS "fair",
			SUM(if(poor_maternity_department = '1', 1, 0)) AS "poor",
			SUM(if(very_poor_maternity_department = '1', 1, 0)) AS "very_poor"   
			from  `tabOut-patient questionnaire` 

			WHERE creation BETWEEN "{_from}" AND "{to}" 
	
		;""", as_dict=1)

		# frappe.errprint(data)
	return data
	
def get_columns():
	columns = [
		{
			"label": ("Date"),
			"fieldtype": "Data",
			"fieldname": "date",
			
			"width": 150,
		},
		{
			"label": ("Very Good"),
			"fieldtype": "Data",
			"fieldname": "very_good",
			
			"width": 100,
		},
		{
			"label": ("Consulation Good"),
			"fieldtype": "Data",
			"fieldname": "good",
			
			"width": 200,
		},
			{
			"label": ("Consultation fair"),
			"fieldtype": "Data",
			"fieldname": "fair",
			
			"width": 200,
		},
	
		{
			"label": ("Consultation Poor"),
			"fieldtype": "Data",
			"fieldname": "poor",
			
			"width": 150,
		},
		{
			"label": ("Consultation Very Poor"),
			"fieldtype": "int",
			"fieldname": "very_poor",
			
			"width": 200,
		}
	
	
	]
	return columns