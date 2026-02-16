import frappe
import pandas as pd
from frappe.utils import getdate
def create_rooms():
	df = pd.read_excel(r'/home/rasiin/frappe-bench/Shift.xlsx')
   

	df= pd.DataFrame(df)
	data = df.to_dict(orient='records')
	formatted_data = []
	for item in data:
		formatted_item = {'Empoloyee': item['Empoloyee']}
		shifts = {}
		for key, value in item.items():
			if key != 'Empoloyee' and key != 'Employee Name':
				shifts[key] = value
		formatted_item['shifts'] = shifts
		formatted_data.append(formatted_item)
	# print(formatted_data)
	shift = ''
	for f_data in formatted_data:
		# print(f_data['Empoloyee'])
		for key , value in f_data['shifts'].items():
				print( frappe.db.get_value("Employee" , f_data['Empoloyee'] , "employee_name"), value)
				# print(formatted_item)
				# try:
					# if type(value) == "str":
				value = str(value).strip()
				if value == "D":
					shift = "Day Shift"
				if value == "N":
					shift = "Night Shift"
				if value == "DN":
					shift = "Day and Night Shift"
				if value=="ND":
					shift= "Night Day Shift"
				if value=="CANTEEN":
					shift ="CANTEEN"
				if value=="EN":
					shift ="Exception Night shift"
				if value=="ED":
					shift ="Exception Day Shift"
		
				if value:
					if value.upper() ==  "OFF" or value.upper() == "OF": 
						shift = "Free"
						
				# except:
				# 	print(formatted_item)
				shift_date = f"2024-07-{key}"
			# print(key , value)
				try:
					shce_doc = frappe.get_doc(
						{
								"doctype": 'Employee Schedulling',
								"employee": f_data['Empoloyee'],
								"employee_name" : frappe.db.get_value("Employee" , f_data['Empoloyee'] , "employee_name"),
								"shift" : shift,
								"from_date" : getdate(shift_date),
								"to_date" : getdate(shift_date),
								"day": key,
								"label" : shift_date,
								"month" : "July",
								"year" : "2024"
								
					}
					)
					shce_doc.insert()
				except Exception as error:
					print(error) 

				# print(frappe.utils.getdate(f"2023-7-{key}") , value)
	frappe.db.commit()		
		
	# for d in data:
		# print()
		
		# if not frappe.db.exists("Healthcare Service Unit Type" ,d['Service Unit Type']):
		#     # service_type = frappe.get_doc("Healthcare Service Unit Type")
		#     room_dict = {"doctype" : "Healthcare Service Unit Type"}
		#     for key , val in d.items():
		#     # [{'Service Unit Type': 'Room 14', 'Type': 'IPD', 'Allow Overlap': 0, 'Inpatient Occupancy': 1, 'Is Billable': 1, 'Item Code': 'Room 14', 'Item Group': 'Room', 'UOM': 'Hour', 'UOM Conversion in Hours': 24, 'Rate / UOM': 20, 'Description': 'Room 14'}, {'Service Unit Type': 'Emergency', 'Type': 'IPD', 'Allow Overlap': 0, 'Inpatient Occupancy': 1, 'Is Billable': 1, 'Item Code': 'Emergency', 'Item Group': 'Room', 'UOM': 'Hour', 'UOM Conversion in Hours': 24, 'Rate / UOM': 20, 'Description': 'Emergency'}
		#         # print("Creating OPD Service Unit")
		#         doc_f = frappe.get_meta("Healthcare Service Unit Type")
				
		#         for f in doc_f.fields:
		#             if f.label == key:
		#                 # print(val)
		#                 room_dict[f.fieldname] = val
		#     # print(room_dict)
		#     service_type = frappe.get_doc(room_dict)
		#     service_type.insert()
			 
					
			
		
		# print("Done")

