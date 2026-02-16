import  frappe
@frappe.whitelist()
def steps(doctor,doc, method=None):
	b = frappe.db.sql(f""" 
	select min(token_no) as min,
	practitioner,name,patient,
	patient_encounter,que_steps 
	from `tabQue` 
	where date =current_date 
	and practitioner='{doctor}' 
	and que_steps != "Called"
	and status="Open"
	  """ 
	, as_dict = True)
	que_doc = frappe.get_doc("Que" , doc)
	que_doc.que_steps="Called"
	que_doc.save()
	return b
		# num = b[0]['max'] 
		# if num == None:
		# 	num = 0
		# frappe.msgprint(int(num)+1)
		# doc.token = int(num) + 1
@frappe.whitelist()
def missed(doctor,doc, method=None):
	b = frappe.db.sql(f""" 
	select min(token_no) as min,
	practitioner,name,patient,
	patient_encounter,que_steps 
	from `tabQue` 
	where date = current_date 
	and practitioner='{doctor}' 
	and que_steps != "Called"
	and status="Open"
	  """ 
	, as_dict = True)
	que_doc = frappe.get_doc("Que" , doc)
	que_doc.que_steps="Missed"
	que_doc.save()
	
	return b


@frappe.whitelist()
def All_que_numbers(doctor = None,method=None):
	# frappe.msgprint(doctor)
	sql = frappe.db.sql(f""" 
	select COUNT(token_no) as number
	from `tabQue` 
	where date =current_date()
	and practitioner='{doctor}'
	and status="Open" 
	 
	
	  """ 
	, as_dict = True)
	# frappe.msgprint(str(b))
	# frappe.errprint(b)
	return sql



