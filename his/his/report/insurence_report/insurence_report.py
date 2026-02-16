# # Copyright (c) 2022, Anfac Tech and contributors
# # For license information, please see license.txt

# import frappe

# def execute(filters=None):
	
#     return get_columns(), get_data(filters)

# def get_data(filters):
	
#     _from ,to  = filters.get('from_date'), filters.get('to') 
	
# # 	data = frappe.db.sql(f"""
# # 	select 
# # 	posting_date,
# # 	name, 
# # 	customer ,
# # 	insurance,
# # 	insurance_id, 
# # 	outstanding_amount


# # from `tabSales Invoice`
# # where posting_date between "{_from}" and "{to}" 
# # and outstanding_amount > 0 and docstatus=1 and is_insurance=1 GROUP BY insurance
# #  ;""")
#     data = frappe.db.sql(f"""
#       SELECT 
# 	posting_date,
# 	name, 
# 	customer,
# 	insurance,
# 	insurance_id, 
# 	outstanding_amount,
# 	SUM(outstanding_amount) AS total_amount
# FROM `tabSales Invoice`
# WHERE posting_date BETWEEN '{_from}' AND '{to}' 
# 	AND outstanding_amount > 0 
# 	AND docstatus = 1 
# 	AND is_insurance = 1 
# GROUP BY insurance, customer
# ORDER BY insurance, posting_date


#     """)
#     return data
# def get_columns():
#     return [

#         "Date: Date:120",
#         "Voucher:Link/Sales Invoice:220",
#         "Customer Name:Link/Customer:200",
#         "insurance:Data/insurance:180",
#         "insurance ID:Data/insurance:150", 
#         "Amount:Currency:110",
	
		
#     ]


# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils import add_to_date
def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
	_from, to = filters.get('from_date'), filters.get('to')

	data = frappe.db.sql(f"""
		SELECT
			insurance,
			customer,
			outstanding_amount
		FROM
			`tabSales Invoice`
		WHERE
			posting_date BETWEEN '{_from}' AND '{to}'
			AND outstanding_amount > 0
			AND docstatus = 1
			AND is_insurance = 1
		GROUP BY
			customer, insurance
		ORDER BY
			insurance, customer
	""", as_dict=True)

	result = []
	current_insurance = None
	total = 0

	for row in data:
		if row.insurance != current_insurance:
			if current_insurance:
				# append the total for the previous insurance company
				result.append({
					"insurance": party_mobile,
					"mobile": party_mobile,
					"balance": total
				})
				total = 0
			party = row.customer
			party_mobile = frappe.get_value("Contact",party+"-"+party,"mobile_no")

		# append the row for the customer
		result.append({
			"insurance": "",
			"customer": row.customer,
			"mobile": row.customer_mobile,
			"balance": row.outstanding_amount
		})

		total += row.outstanding_amount

	# add the last insurance company's total
	if current_insurance:
		result.append({
			"insurance": party_mobile,
			"mobile": party_mobile,
			"balance": total
		})

	return result


def get_columns():
	columns = [

{
			"label": _("insurance"),
			"fieldtype": "Data",
			"fieldname": "insurance",
			"width": 100,
		},
		{
			"label": _("Customer"),
			"fieldtype": "Data",
			"fieldname": "customer",
			"width": 300,
		},
		{
			"label": _("Mobile"),
			"fieldtype": "Data",
			"fieldname": "mobile",
			
			"width": 200,
		},
			
		
		
			{
			"label": _("Balance"),
			"fieldtype": "Currency",
			"fieldname": "balance",
			
			"width": 100,
		},

		# {
		# 	"label": _("Credit"),
		# 	"fieldtype": "Currency",
		# 	"fieldname": "credit",
			
		# 	"width": 100,
		# },
			
	]

	return columns



