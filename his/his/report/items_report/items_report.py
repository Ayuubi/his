# Copyright (c) 2022, Anfac and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils import add_to_date
from frappe.utils import date_diff
def execute(filters=None):
	columns, data = [], []
	return get_columns(), get_data()


def get_data():
	batch = frappe.db.sql(f""" 
	
	select 
	item_name,
	expiry_date,
	batch_qty
	from `tabBatch`
	
	""" , as_dict = 1)
	items = []
	for item in batch:
		if  item.expiry_date < getdate() and  item.batch_qty < 0:
			pass
		else:
			days = date_diff(item.expiry_date  , getdate())
			if days <= 0:
					items.append({
						"item":f"<p class = 'bg-danger text-white' >{item.item_name} </p>",
						"expire" : f"<p class = 'bg-danger text-white' >{item.expiry_date}</p>",
						"days" : f"<p class = 'bg-danger text-white' >{date_diff(item.expiry_date  , getdate())} </p>",
						"qty" :f"<p class = 'bg-danger text-white' >{item.batch_qty}</p>"



					})
			elif days <= 30:

				items.append({
					"item":f"<p class = 'bg-warning text-white' >{item.item_name} </p>",
					"expire" : f"<p class = 'bg-warning text-white' >{item.expiry_date}</p>",
					"days" : f"<p class = 'bg-warning text-white' >{date_diff(item.expiry_date  , getdate())} </p>",
					"qty" :f"<p class = 'bg-warning text-white' >{item.batch_qty}</p>"



				})
			else:
				items.append({
					"item": item.item_name,
					"expire" : item.expiry_date,
					"days" : date_diff(item.expiry_date  , getdate()),
					"qty" : item.batch_qty



				})
	return items
def get_columns():
	columns = [




		{
			"label": _("Item"),
			"fieldtype": "Data",
			"fieldname": "item",
			
			
			"width": 300,
		},
	
		
		
		# 	{
		# 	"label": _("Account"),
		# 	"fieldtype": "Data",
		# 	"fieldname": "account",
			
		# 	"width": 200,
		# },
		
			{
			"label": _("Expire Date"),
			"fieldtype": "Data",
			"fieldname": "expire",
			
			"width": 300,
		},
			
		
		
			{
			"label": _("Remaining Days"),
			"fieldtype": "Data",
			"fieldname": "days",
			
			"width": 200,
		},

		{
			"label": _("QTY"),
			"fieldtype": "Data",
			"fieldname": "qty",
			
			"width": 100,
		},
			
	]

	return columns

