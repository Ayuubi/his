import frappe
# import pandas as pd
# import mysql.connector

# create a connection to the MySQL database
# cnx = mysql.connector.connect(user='root', password='Rasiin@2023@',
# 							  host='localhost',
# 							  database='_ce4c0819cb400e95')



# def my_dynamic_view(context , hdynamic_valueall ):
# 	# context.details=frappe.db.get_list('Healthcare Practitioner',fields=['first_name', 'doctor_room','department' ] )
# 	# frappe.errprint(context)
# 	return context
# 	# context.details=frappe.db.get_list('Que',fields=['name', 'patient_id'])
# 	# # frappe.errprint(context)
	
# 	# return context
# routes = [
#      {'method': 'GET', 'path': '/screen/screen/<dynamic_value>', 'handler': my_dynamic_view},
# 	]

def get_context(context):
	return context


@frappe.whitelist()
def get_doctors():
	hall =  str(frappe.form_dict.hall)
	# frappe.msgprint(hall)
	# return hall
# 	doctors=frappe.db.get_all('Healthcare Practitioner',fields=['practitioner_name', 'doctor_room','department' ],order_by='doctor_room', )
	
# 	que=frappe.db.get_all('Que',
# 	filters={
# 		'status': 'Open',
# 		"date" :frappe.utils.getdate(),
# 		# "que_steps" : "Waiting"
# 	},
# 	fields=['token_no', 'patient_name','practitioner_name' , "que_steps"],
# 	order_by = 'modified desc'

	
# )

	# que=frappe.db.get_list('Que',{fields:['patient_id', 'patient_name' ],
	# 	filters:{
	# 	"status":"Open"
	# 	"date":frappe.utils.getdate()
	# 	}
	#  })

	query = f"""
	SELECT 
	practitioner_name ,
	  doctor_room ,
	  department ,
	  break
		FROM `tabHealthcare Practitioner`
		where doctor_hall = '{hall}'
		"""

	# read data into a pandas dataframe
	doctors = frappe.db.sql(query , as_dict = 1)
	# doctors = doctors.to_dict(orient='records')
	# close the database connection
	query_que = """SELECT 
	practitioner_name,
	token_no,
	patient_name,
	practitioner_name,
	que_steps
		FROM `tabQue`
		where date = current_date() and status = "Open"  and que_steps != "Called"
		
		order by  modified desc
		
		"""
	que =frappe.db.sql(query_que , as_dict = 1)
	

	
	called_que = """SELECT 
	practitioner_name,
	token_no,
	patient_name,
	practitioner_name,
	que_steps
		FROM `tabQue`
		where date = current_date() and status = "Open"  and que_steps = "Called"
		
		order by  modified asc
		
		"""
	c_que = frappe.db.sql(called_que , as_dict = 1)
	

	# cnx.close()

	by_doc_call = {}
	by_doc_call_list = []
	for i in c_que:
		
		by_doc_call[i["practitioner_name"]] = i
		by_doc_call_list.append(by_doc_call)

	return que,doctors , by_doc_call


@frappe.whitelist()
def get_collection():

	# frappe.msgprint(hall)
	# return hall
# 	doctors=frappe.db.get_all('Healthcare Practitioner',fields=['practitioner_name', 'doctor_room','department' ],order_by='doctor_room', )
	
# 	que=frappe.db.get_all('Que',
# 	filters={
# 		'status': 'Open',
# 		"date" :frappe.utils.getdate(),
# 		# "que_steps" : "Waiting"
# 	},
# 	fields=['token_no', 'patient_name','practitioner_name' , "que_steps"],
# 	order_by = 'modified desc'

	
# )

	# que=frappe.db.get_list('Que',{fields:['patient_id', 'patient_name' ],
	# 	filters:{
	# 	"status":"Open"
	# 	"date":frappe.utils.getdate()
	# 	}
	#  })


	# doctors = doctors.to_dict(orient='records')
	# close the database connection
	query_que = """SELECT 
	token_no,
	patient_name,

	
	que_steps
		FROM `tabSample Collection`
		where date = current_date()  and que_steps != "Called"
		
		order by  modified desc
		
		"""
	que =frappe.db.sql(query_que , as_dict = 1)
	

	
	called_que = """SELECT 
	
	token_no,
	patient_name,
	
	que_steps
		FROM `tabSample Collection`
		where date = current_date()  and que_steps = "Called"
		
		order by  modified desc
		
		"""
	c_que = frappe.db.sql(called_que , as_dict = 1)
	

	# cnx.close()


	return que , c_que


@frappe.whitelist()
def is_user_logged_in(user):
	pass
	# session = frappe.db.get_value("tabSessions", filters={"user": "cashier@testdomain.com"}, fieldname=["sessiondata", "session_expiry"])
	# if session and session[0] and session[1] and session[1] > frappe.utils.now():
	# 	print("Session of user cashier@testdomain.com is active")
	# else:
	# 	print("Session of user cashier@testdomain.com is not active")

	# 	return session
	
# 	sessions = frappe.db.sql(f"""SELECT * FROM `tabSessions` WHERE  user = "{user}" and lastupdate < DATE_SUB(NOW(), INTERVAL 1
# MINUTE)""", as_dict=True)
	# return session