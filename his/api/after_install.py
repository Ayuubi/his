import frappe
def after_install():
    translate_gender()
    delate_genders()
    accounts_creations()
    Create_mode_of_payment()
    sources_creations()
    roles_creations()
    frappe.db.commit()

def translate_gender():
    if not frappe.db.exists("Translation" , {"source_text" : "Gender"  , "translated_text" : "Sex"}):
        translate_gender = frappe.get_doc({
            "doctype" : "Translation",
            "language" : "en",
            "source_text" : "Gender",
            "translated_text" : "Sex"
        })
    
        translate_gender.save()
        frappe.db.commit()

def delate_genders():
    for i in ["Prefer not to say","Non-Conforming","Genderqueer","Transgender","Other"]:
        if frappe.db.exisits("Gender" ,i):
            del_genders = frappe.get_doc("Gender" , i)
            del_genders.delete()
            frappe.db.commit()

def accounts_creations():
   
    for i in ["Discount","Free Que"]:
        if not frappe.db.exisits("Account" ,i+' - '+abbr):
            account_creation = frappe.get_doc({
                "doctype" : "Account",
                "account_name" : i,
                "company" : company,
                "parent_account" : "5000 - Expenses - "+abbr,
                "account_type" : "Cash"
            })
    
            account_creation.save()
            frappe.db.commit()   


def Create_mode_of_payment():
  
    mode_of_payment = frappe.get_doc({
        "doctype" : "Mode of Payment",
        "mode_of_payment" : "Free",
        "type" : "Cash",
        "accounts" : [{
            "company": frappe.defaults.get_user_default("company"),
            "default_account": "Free Que - "+ abbr
        }]
    })
   
    mode_of_payment.save()
    frappe.db.commit()    

def sources_creations():
    for i in ["IPD","OPD","WP","E.R", "PACKAGE", ]:
         if not frappe.db.exisits("Source Order" ,i):
            source_creation = frappe.get_doc({
                "doctype" : "Source Order",
                "source" : i
            })
    
            source_creation.save()
            frappe.db.commit()   

def roles_creations():
    for i in ["Tafaariiq"]:
         if not frappe.db.exisits("Role" ,i):
            role_creation = frappe.get_doc({
                "doctype" : "Role",
                "role_name" : i
            })
    
            role_creation.save()
            frappe.db.commit()
 

def uom_creations():
    for i in ["Strep"]:
        if not frappe.db.exisits("UOM" ,i):
            uom_creation = frappe.get_doc({
                "doctype" : "UOM",
                "uom_name" : i,
                "must_be_whole_number" : 0
            })
    
            uom_creation.save()
            frappe.db.commit()
