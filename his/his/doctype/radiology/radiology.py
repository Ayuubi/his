# Copyright (c) 2022, Rasiin and contributors
# For license information, please see license.txt

import frappe
from frappe.utils  import getdate
from frappe.model.document import Document
from his.api.revisit import que_revisit
from his.api.send_sms import send_sms

class Radiology(Document):
	def on_submit(self):
		update_check_tests_stat(self)

		name=frappe.db.get_value("Imaging Preparation", {"examination":self.eximination }, "name")
		frappe.db.set_value("Imaging Preparation", name, "status" , 1)  
		# frappe.msgprint(name)
	



def update_check_tests_stat(self):
	if frappe.db.exists("Tests Status Check" , {"patient" : self.patient , "date" : getdate() , "practitioner" : self.practitioner}):
			name = frappe.db.get_value("Tests Status Check" , {"patient" : self.patient , "date" : getdate() , "practitioner" : self.practitioner} , "name")
			pre_sts = frappe.get_doc("Tests Status Check" , name)
			for test in pre_sts.refrence_test:
				if test.test == self.name:
					test.status = "Ready"
			pre_sts.save(ignore_permissions=1)
			complete = True
			for state in pre_sts.refrence_test:
				if state.status == "Not Ready":
					complete = False
					break
			if complete:
				pass
				# frappe.msgprint("Completed")
				# create_revisit_and_send_sms(self)
		
def create_revisit_and_send_sms(self):
	name = frappe.db.get_value("Que" , {"patient" : self.patient , "date" : getdate() , "practitioner" : self.practitioner , "status" : "Closed" } , "name")
	p_number = frappe.db.get_value("Patient" ,self.patient , "mobile_no")
	if name:
			
		# quee=que_revisit(name)
		msg = f"Asc walal waa diyar sheybaarkaaga"
		# send_sms(p_number , msg)
	