import frappe
from his.api.make_invoice import make_credit_invoice
@frappe.whitelist()
def bill_inp():
    ip_occupancy = frappe.db.sql("""select * from `tabInpatient Occupancy` where `left` = 0 ;""" , as_dict = True )
    if ip_occupancy:
        
        for ipo in ip_occupancy:
            ip = frappe.get_doc("Inpatient Record" , ipo.parent)
            if ip.status == "Admitted":
                patientinfo = frappe.get_doc("Patient" , ip.patient)
                service_unit_type = frappe.get_doc("Healthcare Service Unit Type", frappe.db.get_value("Healthcare Service Unit", ipo.service_unit, "service_unit_type"))
                patient = ip.patient
                patient_name = ip.patient_name
                customer = patientinfo.customer
                item_code = service_unit_type.item
                rate = service_unit_type.rate
                desc = service_unit_type.description
                remark = ipo.service_unit
                practitioner = ip.primary_practitioner
                medical_department = ip.medical_department
                # salesdoc = frappe.get_doc({
                        
                        
                #             "patient": patient,
                #             "patient_name": patient_name,
                #             "customer" : customer,
                #             "is_pos" : 0,
                #             "so_type": "Cashiers",
                #             "source_order" : "IPD",
                #             "owner" : "inpatient@mshospital.so",
                
                #             'due_date' : frappe.utils.getdate(),
                        
                #             "remarks" : remark,
                        
                        
                #             "doctype": "Sales Invoice",
                #             "cost_center": "Main - MSH",
                    
                #             "ref_practitioner" : practitioner,
                            
                #             "items": [
                #                 {
                #                 "item_code": item_code,
                #                     "item_name": item_code,
                #                     "description": desc,
                                
                
                #                     "qty": 1,
                
                #                     "rate": rate,
                #                     "amount": 1*rate,
                
                
                
                                
                
                
                    
                
                #                     "doctype": "Sales Invoice Item",
                
                #                 }
                #             ],
                
                #         })
                # try:
                #     salesdoc.insert()
                #     salesdoc.submit()
                # except:
                #     pass
                
                items = []
                # empty_items = ""
                # for item in self.items:

                items.append({
                       "item_code": item_code,
                        "item_name": item_code,
                        "description": desc,
                    
    
                        "qty": 1,
    
                        "rate": rate,
                        "amount": 1*rate,
                
                        
                    })



                    
                
                


                sales_doc = frappe.get_doc({
                    "doctype" : "Sales Order",
                    "so_type": "Cashiers",
                    "transaction_date" : frappe.utils.getdate(),
                    "customer": customer,
                    "patient" : patient,
                
                    # "discout_amount" : doc.discount_amount,
                    
                    # "voucher_no" : doc.name,
                    "source_order" : "IPD",
                    "ref_practitioner" : practitioner,
                    # "additional_discount_percentage": self.additional_discount_percentage,
                    "items" : items,
                
                })

                sales_doc.insert()
                sales_doc.submit()
                sale_inv = make_credit_invoice(sales_doc.name)
                