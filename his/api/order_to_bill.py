import frappe
from erpnext.stock.get_item_details import get_pos_profile
from his.api.make_invoice import make_sales_invoice_direct
from his.api.make_invoice import make_credit_invoice

def create_que_order_bill(doc):
    company = frappe.defaults.get_user_default("company")
    company_doc= frappe.get_doc("Company",company)
    cost_center = company_doc.cost_center
    pos_profile = get_pos_profile(company)
    medical_department = doc.medical_department
    mode_of_payment = doc.mode_of_payment
    
    if not mode_of_payment:

        mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
     
    default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
    # mode_of_payment = "Cash"
    
    customer = frappe.db.get_value("Patient" , doc.patient , "customer")
    items = []
    # empty_items = ""
    # for item in self.items:

    items.append({
            "item_code" : "OPD Consultation",
            "rate" : doc.doctor_amount,
            "qty" : 1,
            
        })
    if doc.bill_to_employee:
        sales_doc = frappe.get_doc({
            "doctype" : "Sales Invoice",
            "patient": doc.patient,
            "posting_date" : doc.date,
            "customer": customer,
            "patient" : doc.patient,
            "cost_center": cost_center,
            "so_type": "Cashiers",
            "is_pos": 1,
            "bill_to_employee": 1,
            "employee": doc.employee,
            "source_order" : "OPD",
            "ref_practitioner" : doc.practitioner,
            "items" : items,
            "discount_amount" : doc.discount,
            "payments" : [{
					"mode_of_payment" : mode_of_payment,
					"amount" :doc.paid_amount
				}]
        
        })

        sales_doc.insert()
        sales_doc.submit()
        # sale_inv = make_sales_invoice_direct(sales_doc.name , doc.paid_amount , mode_of_payment)
        
        # doc.sales_order  = sales_doc.name
        doc.sales_invoice = sales_doc.name
        doc.save()
        return sales_doc
    elif doc.bill_to_insurance:
        sales_doc = frappe.get_doc({
            "doctype" : "Sales Invoice",
            "patient": doc.patient,
            "posting_date" : doc.date,
            "customer": customer,
            "patient" : doc.patient,
            "cost_center": cost_center,
            "so_type": "Cashiers",
            "is_pos": 1,
            "is_insurance": 1,
            "insurance": doc.insurance,
            "source_order" : "OPD",
            "ref_practitioner" : doc.practitioner,
            "items" : items,
            "discount_amount" : doc.discount,
            "payments" : [{
					"mode_of_payment" : mode_of_payment,
					"amount" :doc.paid_amount
				}]
        
        })

        sales_doc.insert()
        sales_doc.submit()
        doc.sales_invoice = sales_doc.name
        doc.save()
        return sales_doc

    else:

        sales_doc = frappe.get_doc({
            "doctype" : "Sales Order",
            "cost_center": cost_center,
            "so_type": "Cashiers",
            "transaction_date" : doc.date,
            "delivery_date": doc.date,
            "customer": customer,
            "patient" : doc.patient,
        
            "discount_amount" : doc.discount,
            
            "voucher_no" : doc.name,
            "source_order" : "OPD",
            "ref_practitioner" : doc.practitioner,
            # "additional_discount_percentage": self.additional_discount_percentage,
            "items" : items,
        
        })

        sales_doc.insert()
        sales_doc.submit()
        sale_inv = make_sales_invoice_direct(sales_doc.name , doc.paid_amount , mode_of_payment)
        
        doc.sales_order  = sales_doc.name
        doc.sales_invoice = sale_inv
        doc.save()
        return sales_doc




def create_inp_order_bill(doc):
    company = frappe.defaults.get_user_default("company")

    # mode_of_payment = "Cash"
    
    customer = frappe.db.get_value("Patient" , doc.patient , "customer")
    items = []
    # empty_items = ""
    # for item in self.items:

    items.append({
            "item_code" : "OPD Consultation",
            "rate" : doc.doctor_amount,
            "qty" : 1,
            
        })



        
    
    


    sales_doc = frappe.get_doc({
        "doctype" : "Sales Order",
        "so_type": "Cashiers",
        "transaction_date" : doc.date,
        "customer": customer,
        "patient" : doc.patient,
    
        # "discout_amount" : doc.discount_amount,
        
        "voucher_no" : doc.name,
        "source_order" : "OPD",
        "ref_practitioner" : doc.practitioner,
        # "additional_discount_percentage": self.additional_discount_percentage,
        "items" : items,
    
    })

    sales_doc.insert()
    sales_doc.submit()
    sale_inv = make_sales_invoice_direct(sales_doc.name , doc.paid_amount)
    
    doc.sales_order  = sales_doc.name
    doc.sales_invoice = sale_inv
    doc.save()
    return sales_doc



