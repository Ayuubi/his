import frappe
from his.api.tests_sts_check import create_tests_sts
@frappe.whitelist()
def create_lab_tests(doc , method = None):
	# lab_test = frappe.get_doc({
	# 'doctype': 'Lab Result',
	# 'patient': doc.patient
	# })
	# lab_test.insert()
	if doc.hajj_screening:
		sam = frappe.get_doc('Hajj Screening', doc.hajj_screening)
	else:
		sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)

	# sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)
	lab_test_itmes = []
	urine_lab_test_itmes = []
	hor_lab_test_itmes = []

	for item in sam.items:
		# if item.item_group == "Laboratory":
		if item.item_group == "Laboratory":
			template = frappe.get_doc("Lab Test Template" , item.item_code)
			# if template.department == "Hormones":

			# 	if template.lab_test_template_type == "Single":
			# 		hor_lab_test_itmes.append(
			# 				{
			# 					"test" : template.lab_test_name,
			# 					"lab_test_name": template.lab_test_name,
			# 					"lab_test_uom": template.lab_test_uom,
			# 					"secondary_uom": template.secondary_uom,
			# 					"conversion_factor": template.conversion_factor,
			# 					"normal_range": template.lab_test_normal_range,
			# 					"require_result_value": 1,
			# 					"allow_blank ":0
			# 				}
			# 			)

			# 	elif template.lab_test_template_type == "Compound":
			# 		hor_lab_test_itmes.append({

						
							
			# 				"test" : template.name

			# 		})
				
			# 		for normal_test_template in template.normal_test_templates:
			# 		# normal = {}
			# 		# if is_group:
			# 		# 	normal.lab_test_event = normal_test_template.lab_test_event
			# 			# else:
			# 			hor_lab_test_itmes.append({

						
			# 				"lab_test_name": normal_test_template.lab_test_event,
							

			# 				"lab_test_uom": normal_test_template.lab_test_uom,
			# 				"secondary_uom": normal_test_template.secondary_uom,
			# 				"conversion_factor": normal_test_template.conversion_factor,
			# 				"normal_range": normal_test_template.normal_range,
			# 				"require_result_value": 1,
			# 				"allow_blank": normal_test_template.allow_blank,
			# 				"template": template.name
			# 			})
			
			
			
			# else:
			if template.department:
				if template.lab_test_template_type == "Single":
					lab_test_itmes.append(
							{
								"test" : template.lab_test_name,
								"lab_test_name": template.lab_test_name,
								"lab_test_uom": template.lab_test_uom,
								"secondary_uom": template.secondary_uom,
								"conversion_factor": template.conversion_factor,
								"normal_range": template.lab_test_normal_range,
								"require_result_value": 1,
								"allow_blank ":0
							}
						)

				# elif template.lab_test_template_type == "Compound":
				# 	group_test = []
				# 	lab_test_itmes.append({

						
							
				# 			"test" : template.name

				# 	})
					
				# 	for normal_test_template in template.normal_test_templates:
				# 		lab_test_itmes.append({

						
							
				# 			"test" : template.name

				# 	})
				# 		# normal = {}
				# 		# if is_group:
				# 		# 	normal.lab_test_event = normal_test_template.lab_test_event
				# 		# else:
				# 		lab_test_itmes.append({

						
				# 			"lab_test_name": normal_test_template.lab_test_event,
							

				# 			"lab_test_uom": normal_test_template.lab_test_uom,
				# 			"secondary_uom": normal_test_template.secondary_uom,
				# 			"conversion_factor": normal_test_template.conversion_factor,
				# 			"normal_range": normal_test_template.normal_range,
				# 			"require_result_value": 1,
				# 			"allow_blank": normal_test_template.allow_blank,
				# 			"template": template.name
				# 		})
				if template.lab_test_template_type == "Compound":
					cbc_lab_test_itmes = []
					# cbc_lab_test_itmes.append({
							
						
					# 		"test" : template.name,
						
					# 		"template": template.name

					# 		})
					# if template.name == "Stool Examination":
					
					for normal_test_template in template.normal_test_templates:
					# normal = {}
					# if is_group:
					# 	normal.lab_test_event = normal_test_template.lab_test_event
						# else:

						cbc_lab_test_itmes.append({

						
							"lab_test_event": normal_test_template.lab_test_event,
							

							"lab_test_uom": normal_test_template.lab_test_uom,
							"secondary_uom": normal_test_template.secondary_uom,
							"conversion_factor": normal_test_template.conversion_factor,
							"normal_range": normal_test_template.normal_range,
							"require_result_value": 1,
							"allow_blank": normal_test_template.allow_blank,
							"template": template.name
						})

					lab_test = frappe.get_doc({
					'doctype': 'Lab Result',
					'patient' : sam.patient,
					'practitioner' : sam.ref_practitioner,
					"invoice_no" : sam.name,
					"lab_ref" : doc.lab_ref,
					"sample_details" : doc.sample_details,
					'normal_test_items' : cbc_lab_test_itmes,
					"template" : template.name,
					"lab_test_name" : template.name,
					"type" : "Group",
					"reff_collection": doc.name
					
					})
					lab_test.insert()

				elif template.lab_test_template_type == "Grouped":
					urine_lab_test_itmes = []

					for normal_test_template in template.lab_test_groups:
						if not normal_test_template.lab_test_template:
							continue

						group_test = frappe.get_doc("Lab Test Template", normal_test_template.lab_test_template)

						# Case 1: grouped child is Single
						if group_test.lab_test_template_type == "Single":
							urine_lab_test_itmes.append({
								# "lab_test_event": group_test.lab_test_name,
								"lab_test_name": group_test.lab_test_name,
								"lab_test_uom": group_test.lab_test_uom,
								"secondary_uom": group_test.secondary_uom,
								"conversion_factor": group_test.conversion_factor,
								"normal_range": group_test.lab_test_normal_range,
								"require_result_value": 1,
								"allow_blank": 0,
								"template": group_test.name
							})

						# Case 2: grouped child is Compound
						elif group_test.lab_test_template_type == "Compound":
							urine_lab_test_itmes.append({
								"test": template.name,
								"lab_test_name": group_test.lab_test_name or group_test.name,
								"template": template.name
							})

							for test in group_test.normal_test_templates:
								urine_lab_test_itmes.append({
									"lab_test_event": test.lab_test_event,
									"lab_test_uom": test.lab_test_uom,
									"secondary_uom": test.secondary_uom,
									"conversion_factor": test.conversion_factor,
									"normal_range": test.normal_range,
									"require_result_value": 1,
									"allow_blank": test.allow_blank,
									"template": group_test.name
								})

					lab_test = frappe.get_doc({
						'doctype': 'Lab Result',
						'patient': sam.patient,
						'practitioner': sam.ref_practitioner,
						"invoice_no": sam.name,
						"lab_ref": doc.lab_ref,
						"sample_details": doc.sample_details,
						'normal_test_items': urine_lab_test_itmes,
						"template": template.name,
						"lab_test_name": template.name,
						"type": "Group",
						"reff_collection": doc.name
					})
					lab_test.insert()


		# 		elif template.lab_test_template_type == "Grouped" : 
					
			
					
		# 			urine_lab_test_itmes = []
		# 			# if template.name == "Stool Examination":
					
		# 			for normal_test_template in template.lab_test_groups:
		# 				# normal = {}
		# 				# if is_group:
		# 				# 	normal.lab_test_event = normal_test_template.lab_test_event
		# 				# else:
		# 				urine_lab_test_itmes.append({
							
						
		# 					"test" : template.name,
		# 					"lab_test_name" : normal_test_template.lab_test_template,
		# 					"template": template.name

		# 					})
		# 				group_test = frappe.get_doc("Lab Test Template" , normal_test_template.lab_test_template)
		# 				for test in group_test.normal_test_templates:
		# 					urine_lab_test_itmes.append({

							
		# 						"lab_test_event": test.lab_test_event,
								
								
		# 						"lab_test_uom": test.lab_test_uom,
		# 						"secondary_uom": test.secondary_uom,
		# 						"conversion_factor": test.conversion_factor,
		# 						"normal_range": test.normal_range,
		# 						"require_result_value": 1,
		# 						"allow_blank": test.allow_blank,
		# 						"template": normal_test_template.lab_test_template
		# 					})

		# 			lab_test = frappe.get_doc({
		# 			'doctype': 'Lab Result',
		# 			'patient' : sam.patient,
		# 			'practitioner' : sam.ref_practitioner,
		# 			"invoice_no" : sam.name,
		# 			"lab_ref" : doc.lab_ref,
		# 			"sample_details" : doc.sample_details,
		# 			'normal_test_items' : urine_lab_test_itmes,
		# 			"template" : template.name,
		# 			"lab_test_name" : template.name,
		# 			"type" : "Group",
		# 			"reff_collection": doc.name
					
		# 			})
		
		# # for item in doc.items:
		# #     create_lab_tests(item.item_code)
		# 			lab_test.insert()


					
		
	
					
	   
	if lab_test_itmes :
		lab_test = frappe.get_doc({
			'doctype': 'Lab Result',
			'patient' : sam.patient,
			'practitioner' : sam.ref_practitioner,
			"invoice_no" : sam.name,
			"lab_ref" : doc.lab_ref,
			'normal_test_items' : lab_test_itmes,
			"type" : "Blood",
			"reff_collection": doc.name,
			"sample_details": doc.sample_details
			
			})
		
		# for item in doc.items:
		#     create_lab_tests(item.item_code)
		lab_test.insert(ignore_permissions = 1)
		# create_tests_sts(lab_test.doctype , lab_test.name)
	if hor_lab_test_itmes:

		ho_lab_test = frappe.get_doc({
					'doctype': 'Lab Result',
					'patient' : sam.patient,
					'practitioner' : sam.ref_practitioner,
					"invoice_no" : sam.name,
					"lab_ref" : doc.lab_ref,
					'normal_test_items' : hor_lab_test_itmes,
					"reff_collection": doc.name,
				
					"type" : "Hormones"
					
					})
		ho_lab_test.insert()


def create_normals(item_code):
		# for item in doc.items:
		#     frappe.errprint(item.item_code)
			# lab_test.normal_toggle = 1
		template = frappe.get_doc("Lab Test Template" , item_code)
		normal = lab_test.append("normal_test_items")
		normal.lab_test_name = template.lab_test_name
		normal.lab_test_uom = template.lab_test_uom
		normal.secondary_uom = template.secondary_uom
		normal.conversion_factor = template.conversion_factor
		normal.normal_range = template.lab_test_normal_range
		normal.require_result_value = 1
		normal.allow_blank = 0


@frappe.whitelist()
def on_cancel_samples(doc, method=None):
    draft_lab_results = frappe.get_all(
        "Lab Result",
        filters={
            "reff_collection": doc.name,
            "docstatus": 0
        },
        pluck="name"
    )

    for name in draft_lab_results:
        frappe.delete_doc("Lab Result", name, ignore_permissions=True)





# import frappe
# from his.api.tests_sts_check import create_tests_sts
# @frappe.whitelist()
# def create_lab_tests(doc , method = None):
#     # lab_test = frappe.get_doc({
#     # 'doctype': 'Lab Result',
#     # 'patient': doc.patient
#     # })
#     # lab_test.insert()
#     if doc.hajj_screening:
#         sam = frappe.get_doc('Hajj Screening', doc.hajj_screening)
#     else:
#         sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)
#     # sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)
#     lab_test_itmes = []
#     urine_lab_test_itmes = []
#     hor_lab_test_itmes = []

#     for item in sam.items:
#         # if item.item_group == "Laboratory":
#         if frappe.db.exists("Lab Test Template", {"item": item.item_code}, cache=True):
#             template = frappe.get_doc("Lab Test Template" , {"item":item.item_code})
#             # if template.department == "Hormones":

#             # 	if template.lab_test_template_type == "Single":
#             # 		hor_lab_test_itmes.append(
#             # 				{
#             # 					"test" : template.lab_test_name,
#             # 					"lab_test_name": template.lab_test_name,
#             # 					"lab_test_uom": template.lab_test_uom,
#             # 					"secondary_uom": template.secondary_uom,
#             # 					"conversion_factor": template.conversion_factor,
#             # 					"normal_range": template.lab_test_normal_range,
#             # 					"require_result_value": 1,
#             # 					"allow_blank ":0
#             # 				}
#             # 			)

#             # 	elif template.lab_test_template_type == "Compound":
#             # 		hor_lab_test_itmes.append({

                        
                            
#             # 				"test" : template.name

#             # 		})
                
#             # 		for normal_test_template in template.normal_test_templates:
#             # 		# normal = {}
#             # 		# if is_group:
#             # 		# 	normal.lab_test_event = normal_test_template.lab_test_event
#             # 			# else:
#             # 			hor_lab_test_itmes.append({

                        
#             # 				"lab_test_name": normal_test_template.lab_test_event,
                            

#             # 				"lab_test_uom": normal_test_template.lab_test_uom,
#             # 				"secondary_uom": normal_test_template.secondary_uom,
#             # 				"conversion_factor": normal_test_template.conversion_factor,
#             # 				"normal_range": normal_test_template.normal_range,
#             # 				"require_result_value": 1,
#             # 				"allow_blank": normal_test_template.allow_blank,
#             # 				"template": template.name
#             # 			})
            
            
            
#             # else:
#             if template.department:
#                 if template.lab_test_template_type == "Single":
#                     lab_test_itmes.append(
#                             {
#                                 "test" : template.lab_test_name,
#                                 "lab_test_name": template.lab_test_name,
#                                 "lab_test_uom": template.lab_test_uom,
#                                 "secondary_uom": template.secondary_uom,
#                                 "conversion_factor": template.conversion_factor,
#                                 "normal_range": template.lab_test_normal_range,
#                                 "require_result_value": 1,
#                                 "allow_blank ":0,
#                                 "sales_invoice_item": item.name
#                             }
#                         )

#                 # elif template.lab_test_template_type == "Compound":
#                 # 	group_test = []
#                 # 	lab_test_itmes.append({

                        
                            
#                 # 			"test" : template.name

#                 # 	})
                    
#                 # 	for normal_test_template in template.normal_test_templates:
#                 # 		lab_test_itmes.append({

                        
                            
#                 # 			"test" : template.name

#                 # 	})
#                 # 		# normal = {}
#                 # 		# if is_group:
#                 # 		# 	normal.lab_test_event = normal_test_template.lab_test_event
#                 # 		# else:
#                 # 		lab_test_itmes.append({

                        
#                 # 			"lab_test_name": normal_test_template.lab_test_event,
                            

#                 # 			"lab_test_uom": normal_test_template.lab_test_uom,
#                 # 			"secondary_uom": normal_test_template.secondary_uom,
#                 # 			"conversion_factor": normal_test_template.conversion_factor,
#                 # 			"normal_range": normal_test_template.normal_range,
#                 # 			"require_result_value": 1,
#                 # 			"allow_blank": normal_test_template.allow_blank,
#                 # 			"template": template.name
#                 # 		})
#                 if template.lab_test_template_type == "Compound":
#                     cbc_lab_test_itmes = []
#                     # cbc_lab_test_itmes.append({
                            
                        
#                     # 		"test" : template.name,
                        
#                     # 		"template": template.name

#                     # 		})
#                     # if template.name == "Stool Examination":
                    
#                     for normal_test_template in template.normal_test_templates:
#                     # normal = {}
#                     # if is_group:
#                     # 	normal.lab_test_event = normal_test_template.lab_test_event
#                         # else:

#                         cbc_lab_test_itmes.append({

                        
#                             "lab_test_event": normal_test_template.lab_test_event,
                            

#                             "lab_test_uom": normal_test_template.lab_test_uom,
#                             "secondary_uom": normal_test_template.secondary_uom,
#                             "conversion_factor": normal_test_template.conversion_factor,
#                             "normal_range": normal_test_template.normal_range,
#                             "require_result_value": 1,
#                             "allow_blank": normal_test_template.allow_blank,
#                             "template": template.name
#                         })

#                     lab_test = frappe.get_doc({
#                     'doctype': 'Lab Result',
#                     'patient' : sam.patient,
#                     'practitioner' : sam.ref_practitioner,
#                     "invoice_no" : sam.name,
#                     "lab_ref" : doc.lab_ref,
#                     "sample_details" : doc.sample_details,
#                     'normal_test_items' : cbc_lab_test_itmes,
#                     "template" : template.name,
#                     "lab_test_name" : template.name,
#                     "type" : "Group",
#                     "reff_collection": doc.name,
#                     "sales_invoice_item": item.name
                    
#                     })
#                     lab_test.insert()

#                 # elif template.lab_test_template_type == "Grouped" : 
                    
            
                    
#                 # 	urine_lab_test_itmes = []
#                 # 	# if template.name == "Stool Examination":
                    
#                 # 	for normal_test_template in template.lab_test_groups:
#                 # 		# normal = {}
#                 # 		# if is_group:
#                 # 		# 	normal.lab_test_event = normal_test_template.lab_test_event
#                 # 		# else:
#                 # 		urine_lab_test_itmes.append({
                            
                        
#                 # 			"test" : template.name,
#                 # 			"lab_test_name" : normal_test_template.lab_test_template,
#                 # 			"template": template.name

#                 # 			})
#                 # 		group_test = frappe.get_doc("Lab Test Template" , normal_test_template.lab_test_template)
#                 # 		for test in group_test.normal_test_templates:
#                 # 			urine_lab_test_itmes.append({

                            
#                 # 				"lab_test_event": test.lab_test_event,
                                
                                
#                 # 				"lab_test_uom": test.lab_test_uom,
#                 # 				"secondary_uom": test.secondary_uom,
#                 # 				"conversion_factor": test.conversion_factor,
#                 # 				"normal_range": test.normal_range,
#                 # 				"require_result_value": 1,
#                 # 				"allow_blank": test.allow_blank,
#                 # 				"template": normal_test_template.lab_test_template
#                 # 			})

#                 # 	lab_test = frappe.get_doc({
#                 # 	'doctype': 'Lab Result',
#                 # 	'patient' : sam.patient,
#                 # 	'practitioner' : sam.ref_practitioner,
#                 # 	"invoice_no" : sam.name,
#                 # 	"lab_ref" : doc.lab_ref,
#                 # 	"sample_details" : doc.sample_details,
#                 # 	'normal_test_items' : urine_lab_test_itmes,
#                 # 	"template" : template.name,
#                 # 	"lab_test_name" : template.name,
#                 # 	"type" : "Group",
#                 # 	"reff_collection": doc.name,
#                 # 	"sales_invoice_item": item.name
                    
#                 # 	})


#                 elif template.lab_test_template_type == "Grouped":

#                     urine_lab_test_itmes = []

#                     for row in template.lab_test_groups:
#                         # each row points to another Lab Test Template (e.g. Sodium, Potassium...)
#                         group_test = frappe.get_doc("Lab Test Template", row.lab_test_template)

#                         urine_lab_test_itmes.append({
#                             # optional: keep parent/group name if your table uses it
#                             "test": template.name,

#                             # IMPORTANT: set the name + normal range in SAME row
#                             "lab_test_name": group_test.lab_test_name or row.lab_test_template,
#                             "lab_test_uom": group_test.lab_test_uom,
#                             "secondary_uom": group_test.secondary_uom,
#                             "conversion_factor": getattr(group_test, "conversion_factor", 1) or 1,
#                             "normal_range": group_test.lab_test_normal_range,

#                             "require_result_value": 1,
#                             "allow_blank": getattr(group_test, "allow_blank", 0) or 0,

#                             # keep reference to the actual template
#                             "template": row.lab_test_template,
#                         })

#                     lab_test = frappe.get_doc({
#                         "doctype": "Lab Result",
#                         "patient": sam.patient,
#                         "practitioner": sam.ref_practitioner,
#                         "invoice_no": sam.name,
#                         "lab_ref": doc.lab_ref,
#                         "sample_details": doc.sample_details,
#                         "normal_test_items": urine_lab_test_itmes,
#                         "template": template.name,
#                         "lab_test_name": template.name,
#                         "type": "Group",
#                         "reff_collection": doc.name,
#                         "sales_invoice_item": item.name
#                     })
#                     lab_test.insert()
#         # for item in doc.items:
#         #     create_lab_tests(item.item_code)


                    
        
    
                    
       
#     if lab_test_itmes :
#         lab_test = frappe.get_doc({
#             'doctype': 'Lab Result',
#             'patient' : sam.patient,
#             'practitioner' : sam.ref_practitioner,
#             "invoice_no" : sam.name,
#             "lab_ref" : doc.lab_ref,
#             'normal_test_items' : lab_test_itmes,
#             "type" : "Blood",
#             "reff_collection": doc.name,
#             "sample_details": doc.sample_details
            
#             })
        
#         # for item in doc.items:
#         #     create_lab_tests(item.item_code)
#         lab_test.insert(ignore_permissions = 1)
#         # create_tests_sts(lab_test.doctype , lab_test.name)
#     if hor_lab_test_itmes:

#         ho_lab_test = frappe.get_doc({
#                     'doctype': 'Lab Result',
#                     'patient' : sam.patient,
#                     'practitioner' : sam.ref_practitioner,
#                     "invoice_no" : sam.name,
#                     "lab_ref" : doc.lab_ref,
#                     'normal_test_items' : hor_lab_test_itmes,
#                     "reff_collection": doc.name,
                    
#                     "type" : "Hormones"
                    
#                     })
#         ho_lab_test.insert()


# def create_normals(item_code):
#         # for item in doc.items:
#         #     frappe.errprint(item.item_code)
#             # lab_test.normal_toggle = 1
#         template = frappe.get_doc("Lab Test Template" , item_code)
#         normal = lab_test.append("normal_test_items")
#         normal.lab_test_name = template.lab_test_name
#         normal.lab_test_uom = template.lab_test_uom
#         normal.secondary_uom = template.secondary_uom
#         normal.conversion_factor = template.conversion_factor
#         normal.normal_range = template.lab_test_normal_range
#         normal.require_result_value = 1
#         normal.allow_blank = 0


# # @frappe.whitelist()
# # def create_lab_result_doc(doc, method=None):
# #     if doc.hajj_screening:
# #         sam = frappe.get_doc('Hajj Screening', doc.hajj_screening)
# #     else:
# #         sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)
# #     # sam = frappe.get_doc("Sales Invoice", doc.reff_invoice)

# #     # Prevent double creation for same sample collection
# #     if frappe.db.exists("Lab Result", {"reff_collection": doc.name}):
# #         return

# #     lab_test_items = []

# #     for item in sam.items:
# #         if not frappe.db.exists("Lab Test Template", {"item": item.item_code}, cache=True):
# #             continue

# #         template = frappe.get_cached_doc("Lab Test Template", {"item": item.item_code})
# #         if not template.department:
# #             continue

# #         # SINGLE -> one combined Lab Result later (Blood)
# #         if template.lab_test_template_type == "Single":
# #             lab_test_items.append({
# #                 "test": template.lab_test_name,
# #                 "lab_test_name": template.lab_test_name,
# #                 "lab_test_uom": template.lab_test_uom,
# #                 "secondary_uom": template.secondary_uom,
# #                 "conversion_factor": template.conversion_factor,
# #                 "normal_range": template.lab_test_normal_range,
# #                 "require_result_value": 1,
# #                 "allow_blank": 0,  # fixed (no trailing space)
# #                 "sales_invoice_item": item.name
# #             })

# #         # COMPOUND -> create a separate Lab Result per template
# #         elif template.lab_test_template_type == "Compound":
# #             rows = []
# #             for nt in template.normal_test_templates:
# #                 rows.append({
# #                     "lab_test_event": nt.lab_test_event,
# #                     "lab_test_name": nt.lab_test_event,   # safe
# #                     "lab_test_uom": nt.lab_test_uom,
# #                     "secondary_uom": nt.secondary_uom,
# #                     "conversion_factor": nt.conversion_factor,
# #                     "normal_range": nt.normal_range,
# #                     "require_result_value": 1,
# #                     "allow_blank": nt.allow_blank,
# #                     "template": template.name
# #                 })

# #             frappe.get_doc({
# #                 "doctype": "Lab Result",
# #                 "patient": sam.patient,
# #                 "practitioner": sam.ref_practitioner,
# #                 "invoice_no": sam.name,
# #                 "lab_ref": doc.lab_ref,
# #                 "sample_details": doc.sample_details,
# #                 "normal_test_items": rows,
# #                 "template": template.name,
# #                 "lab_test_name": template.name,
# #                 "type": "Group",
# #                 "reff_collection": doc.name,
# #                 "sales_invoice_item": item.name
# #             }).insert(ignore_permissions=True)

# #         # GROUPED -> create a separate Lab Result per template
# #         elif template.lab_test_template_type == "Grouped":
# #             rows = []
# #             for g in template.lab_test_groups:
# #                 group_test = frappe.get_cached_doc("Lab Test Template", g.lab_test_template)
# #                 test_name = group_test.lab_test_name or g.lab_test_template

# #                 rows.append({
# #                     "test": template.name,
# #                     "lab_test_event": test_name,   # safe
# #                     "lab_test_name": test_name,    # safe
# #                     "lab_test_uom": group_test.lab_test_uom,
# #                     "secondary_uom": group_test.secondary_uom,
# #                     "conversion_factor": getattr(group_test, "conversion_factor", 1) or 1,
# #                     "normal_range": group_test.lab_test_normal_range,
# #                     "require_result_value": 1,
# #                     "allow_blank": getattr(group_test, "allow_blank", 0) or 0,
# #                     "template": g.lab_test_template
# #                 })

# #             frappe.get_doc({
# #                 "doctype": "Lab Result",
# #                 "patient": sam.patient,
# #                 "practitioner": sam.ref_practitioner,
# #                 "invoice_no": sam.name,
# #                 "lab_ref": doc.lab_ref,
# #                 "sample_details": doc.sample_details,
# #                 "normal_test_items": rows,
# #                 "template": template.name,
# #                 "lab_test_name": template.name,
# #                 "type": "Group",
# #                 "reff_collection": doc.name,
# #                 "sales_invoice_item": item.name
# #             }).insert(ignore_permissions=True)

# #     # Create ONE Blood Lab Result for all SINGLE tests
# #     if lab_test_items:
# #         frappe.get_doc({
# #             "doctype": "Lab Result",
# #             "patient": sam.patient,
# #             "practitioner": sam.ref_practitioner,
# #             "invoice_no": sam.name,
# #             "lab_ref": doc.lab_ref,
# #             "sample_details": doc.sample_details,
# #             "normal_test_items": lab_test_items,
# #             "type": "Blood",
# #             "reff_collection": doc.name
# #         }).insert(ignore_permissions=True)


# # def _resolve_sales_invoice_context(sample_collection_doc, sam):
# # 	"""
# # 	Return (invoice_name, is_return)
# # 	- If sam is Sales Invoice: use sam
# # 	- If sam is Hajj Screening: use Sample Collection reff_invoice (best), else try sam.ref_invoice / sam.reff_invoice
# # 	"""
# # 	if sam.doctype == "Sales Invoice":
# # 		invoice = sam.name
# # 		is_return = sam.is_return or 0
# # 		return invoice, is_return

# # 	# Prefer Sample Collection link (because you already set it when creating the sample)
# # 	invoice = getattr(sample_collection_doc, "reff_invoice", "") or ""
# # 	if not invoice:
# # 		invoice = getattr(sam, "ref_invoice", "") or getattr(sam, "reff_invoice", "") or ""

# # 	is_return = 0
# # 	if invoice and frappe.db.exists("Sales Invoice", invoice):
# # 		is_return = frappe.db.get_value("Sales Invoice", invoice, "is_return") or 0

# # 	return invoice, is_return


# # def _resolve_sales_invoice_item(sample_collection_doc, sam, item, invoice):
# # 	"""
# # 	Return a valid Sales Invoice Item rowname or None.
# # 	- If sam is Sales Invoice: item.name is correct
# # 	- If sam is Hajj Screening: map using invoice + item_code
# # 	"""
# # 	if sam.doctype == "Sales Invoice":
# # 		return item.name

# # 	if not invoice:
# # 		return None

# # 	return frappe.db.get_value(
# # 		"Sales Invoice Item",
# # 		{"parent": invoice, "item_code": item.item_code},
# # 		"name"
# # 	)


# # @frappe.whitelist()
# # def create_lab_result_doc(doc, method=None):
# # 	# doc is Sample Collection

# # 	# 1) Resolve source doc
# # 	if doc.hajj_screening:
# # 		sam = frappe.get_doc("Hajj Screening", doc.hajj_screening)
# # 	else:
# # 		sam = frappe.get_doc("Sales Invoice", doc.reff_invoice)

# # 	# 2) Prevent double creation for same sample collection
# # 	if frappe.db.exists("Lab Result", {"reff_collection": doc.name}):
# # 		return

# # 	# 3) Resolve invoice context (important when sam is Hajj Screening)
# # 	invoice_no, is_return = _resolve_sales_invoice_context(doc, sam)

# # 	# Optional: skip if return (same style you used elsewhere)
# # 	# If you DO want to allow returns, remove this block.
# # 	if is_return:
# # 		return

# # 	lab_test_items = []

# # 	for item in (sam.items or []):
# # 		if not frappe.db.exists("Lab Test Template", {"item": item.item_code}, cache=True):
# # 			continue

# # 		template = frappe.get_cached_doc("Lab Test Template", {"item": item.item_code})
# # 		if not template.department:
# # 			continue

# # 		# ✅ Map to real Sales Invoice Item when source is Hajj Screening
# # 		si_item = _resolve_sales_invoice_item(doc, sam, item, invoice_no)

# # 		# SINGLE -> one combined Lab Result later (Blood)
# # 		if template.lab_test_template_type == "Single":
# # 			row = {
# # 				"test": template.lab_test_name,
# # 				"lab_test_name": template.lab_test_name,
# # 				"lab_test_uom": template.lab_test_uom,
# # 				"secondary_uom": template.secondary_uom,
# # 				"conversion_factor": template.conversion_factor,
# # 				"normal_range": template.lab_test_normal_range,
# # 				"require_result_value": 1,
# # 				"allow_blank": 0,
# # 			}
# # 			if si_item:
# # 				row["sales_invoice_item"] = si_item

# # 			lab_test_items.append(row)

# # 		# COMPOUND -> create a separate Lab Result per template
# # 		elif template.lab_test_template_type == "Compound":
# # 			rows = []
# # 			for nt in template.normal_test_templates:
# # 				rows.append({
# # 					"lab_test_event": nt.lab_test_event,
# # 					"lab_test_name": nt.lab_test_event,
# # 					"lab_test_uom": nt.lab_test_uom,
# # 					"secondary_uom": nt.secondary_uom,
# # 					"conversion_factor": nt.conversion_factor,
# # 					"normal_range": nt.normal_range,
# # 					"require_result_value": 1,
# # 					"allow_blank": nt.allow_blank,
# # 					"template": template.name
# # 				})

# # 			payload = {
# # 				"doctype": "Lab Result",
# # 				"patient": sam.patient,
# # 				"practitioner": sam.ref_practitioner,
# # 				"invoice_no": invoice_no or sam.name,
# # 				"lab_ref": doc.lab_ref,
# # 				"sample_details": doc.sample_details,
# # 				"normal_test_items": rows,
# # 				"template": template.name,
# # 				"lab_test_name": template.name,
# # 				"type": "Group",
# # 				"reff_collection": doc.name,
# # 			}
# # 			if si_item:
# # 				payload["sales_invoice_item"] = si_item

# # 			frappe.get_doc(payload).insert(ignore_permissions=True)

# # 		# GROUPED -> create a separate Lab Result per template
# # 		elif template.lab_test_template_type == "Grouped":
# # 			rows = []
# # 			for g in template.lab_test_groups:
# # 				group_test = frappe.get_cached_doc("Lab Test Template", g.lab_test_template)
# # 				test_name = group_test.lab_test_name or g.lab_test_template

# # 				rows.append({
# # 					"test": template.name,
# # 					"lab_test_event": test_name,
# # 					"lab_test_name": test_name,
# # 					"lab_test_uom": group_test.lab_test_uom,
# # 					"secondary_uom": group_test.secondary_uom,
# # 					"conversion_factor": getattr(group_test, "conversion_factor", 1) or 1,
# # 					"normal_range": group_test.lab_test_normal_range,
# # 					"require_result_value": 1,
# # 					"allow_blank": getattr(group_test, "allow_blank", 0) or 0,
# # 					"template": g.lab_test_template
# # 				})

# # 			payload = {
# # 				"doctype": "Lab Result",
# # 				"patient": sam.patient,
# # 				"practitioner": sam.ref_practitioner,
# # 				"invoice_no": invoice_no or sam.name,
# # 				"lab_ref": doc.lab_ref,
# # 				"sample_details": doc.sample_details,
# # 				"normal_test_items": rows,
# # 				"template": template.name,
# # 				"lab_test_name": template.name,
# # 				"type": "Group",
# # 				"reff_collection": doc.name,
# # 			}
# # 			if si_item:
# # 				payload["sales_invoice_item"] = si_item

# # 			frappe.get_doc(payload).insert(ignore_permissions=True)

# # 	# Create ONE Blood Lab Result for all SINGLE tests
# # 	if lab_test_items:
# # 		frappe.get_doc({
# # 			"doctype": "Lab Result",
# # 			"patient": sam.patient,
# # 			"practitioner": sam.ref_practitioner,
# # 			"invoice_no": invoice_no or sam.name,
# # 			"lab_ref": doc.lab_ref,
# # 			"sample_details": doc.sample_details,
# # 			"normal_test_items": lab_test_items,
# # 			"type": "Blood",
# # 			"reff_collection": doc.name
# # 		}).insert(ignore_permissions=True)


# import frappe
# from his.api.ref_utils import resolve_sales_invoice_item

# @frappe.whitelist()
# def create_lab_result_doc(doc, method=None):
# 	# doc is Sample Collection

# 	if doc.hajj_screening:
# 		sam = frappe.get_doc("Hajj Screening", doc.hajj_screening)
# 	else:
# 		sam = frappe.get_doc("Sales Invoice", doc.reff_invoice)

# 	if frappe.db.exists("Lab Result", {"reff_collection": doc.name}):
# 		return

# 	lab_test_items = []

# 	for item in (sam.items or []):
# 		if not frappe.db.exists("Lab Test Template", {"item": item.item_code}, cache=True):
# 			continue

# 		template = frappe.get_cached_doc("Lab Test Template", {"item": item.item_code})
# 		if not template.department:
# 			continue

# 		# ✅ Always resolve SI item correctly
# 		si_item = resolve_sales_invoice_item(sam, item, doc.reff_invoice)

# 		if template.lab_test_template_type == "Single":
# 			row = {
# 				"test": template.lab_test_name,
# 				"lab_test_name": template.lab_test_name,
# 				"lab_test_uom": template.lab_test_uom,
# 				"secondary_uom": template.secondary_uom,
# 				"conversion_factor": template.conversion_factor,
# 				"normal_range": template.lab_test_normal_range,
# 				"require_result_value": 1,
# 				"allow_blank": 0,
# 			}
# 			if si_item:
# 				row["sales_invoice_item"] = si_item

# 			lab_test_items.append(row)

# 		elif template.lab_test_template_type == "Compound":
# 			rows = []
# 			for nt in template.normal_test_templates:
# 				rows.append({
# 					"lab_test_event": nt.lab_test_event,
# 					"lab_test_name": nt.lab_test_event,
# 					"lab_test_uom": nt.lab_test_uom,
# 					"secondary_uom": nt.secondary_uom,
# 					"conversion_factor": nt.conversion_factor,
# 					"normal_range": nt.normal_range,
# 					"require_result_value": 1,
# 					"allow_blank": nt.allow_blank,
# 					"template": template.name
# 				})

# 			payload = {
# 				"doctype": "Lab Result",
# 				"patient": sam.patient,
# 				"practitioner": sam.ref_practitioner,
# 				"invoice_no": doc.reff_invoice or sam.name,
# 				"lab_ref": doc.lab_ref,
# 				"sample_details": doc.sample_details,
# 				"normal_test_items": rows,
# 				"template": template.name,
# 				"lab_test_name": template.name,
# 				"type": "Group",
# 				"reff_collection": doc.name,
# 			}
# 			if si_item:
# 				payload["sales_invoice_item"] = si_item

# 			frappe.get_doc(payload).insert(ignore_permissions=True)

# 		elif template.lab_test_template_type == "Grouped":
# 			rows = []
# 			for g in template.lab_test_groups:
# 				group_test = frappe.get_cached_doc("Lab Test Template", g.lab_test_template)
# 				test_name = group_test.lab_test_name or g.lab_test_template

# 				rows.append({
# 					"test": template.name,
# 					"lab_test_event": test_name,
# 					"lab_test_name": test_name,
# 					"lab_test_uom": group_test.lab_test_uom,
# 					"secondary_uom": group_test.secondary_uom,
# 					"conversion_factor": getattr(group_test, "conversion_factor", 1) or 1,
# 					"normal_range": group_test.lab_test_normal_range,
# 					"require_result_value": 1,
# 					"allow_blank": getattr(group_test, "allow_blank", 0) or 0,
# 					"template": g.lab_test_template
# 				})

# 			payload = {
# 				"doctype": "Lab Result",
# 				"patient": sam.patient,
# 				"practitioner": sam.ref_practitioner,
# 				"invoice_no": doc.reff_invoice or sam.name,
# 				"lab_ref": doc.lab_ref,
# 				"sample_details": doc.sample_details,
# 				"normal_test_items": rows,
# 				"template": template.name,
# 				"lab_test_name": template.name,
# 				"type": "Group",
# 				"reff_collection": doc.name,
# 			}
# 			if si_item:
# 				payload["sales_invoice_item"] = si_item

# 			frappe.get_doc(payload).insert(ignore_permissions=True)

# 	if lab_test_items:
# 		frappe.get_doc({
# 			"doctype": "Lab Result",
# 			"patient": sam.patient,
# 			"practitioner": sam.ref_practitioner,
# 			"invoice_no": doc.reff_invoice or sam.name,
# 			"lab_ref": doc.lab_ref,
# 			"sample_details": doc.sample_details,
# 			"normal_test_items": lab_test_items,
# 			"type": "Blood",
# 			"reff_collection": doc.name
# 		}).insert(ignore_permissions=True)


# @frappe.whitelist()
# def on_cancel_samples(doc, method=None):
#     draft_lab_results = frappe.get_all(
#         "Lab Result",
#         filters={
#             "reff_collection": doc.name,
#             "docstatus": 0
#         },
#         pluck="name"
#     )

#     for name in draft_lab_results:
#         frappe.delete_doc("Lab Result", name, ignore_permissions=True)
