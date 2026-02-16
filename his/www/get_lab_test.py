import frappe
@frappe.whitelist(allow_guest = True)
def get_lab_doc(name):
	doc = frappe.get_doc("Lab Result" , name)
	return doc


@frappe.whitelist()
def get_ot_rooms():
	room =  str(frappe.form_dict.room)
	query = f"""
	SELECT 
	service_unit_type ,
	  patient ,
	  patient_name

		FROM `tabHealthcare Service Unit Type`
		where room = '{room}'
		"""

	# read data into a pandas dataframe
	ot_room = frappe.db.sql(query , as_dict = 1)
	return ot_room 

@frappe.whitelist(allow_guest = True)
def get_file(name):
	files = frappe.db.get_list('File',
    filters={
        'attached_to_name': name
    },
    fields=['file_url'],
 
  
    page_length=1000,
  
)

	return files
