from __future__ import unicode_literals
from genericpath import exists
from pickle import FRAME

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

company = frappe.defaults.get_global_default("company")
abbr = frappe.get_value("Company", company, "abbr")
custom_rol_workpace = ["Cashier", "Pharmacy", "Doctor","Full Admin", "Imaging","Nurse"]
sales_users = ["Cashier", "Pharmacy"]
item_groups = ["Laboratory", "OT", "Imaging", "Drug", "Consultation" ,"Procedures"]
defualt_warehouse = frappe.db.get_single_value(
    'Stock Settings', 'default_warehouse')
write_of_account = frappe.db.get_value('Company', company, 'write_off_account')
cost_center = frappe.db.get_value('Company', company, 'round_off_cost_center')


def after_install():
    make_custom_fields()
    make_custom_roles()
    make_property_setters()
    set_system_setting()
    create_users()

    selling_setting()
    healthcare_setting()
    accounting_setting()
    website_setting()

    create_account_for_item_group()
    create_item_groups()
    create_consultation_item()

    # Make sure the accounts exist first
    accounts_creations()
    create_his_accounts()
    # (optionally create_cash_accounts() here if you plan to use it)

    # Now it’s safe to link those accounts
    create_mode_of_payment()
    Create_mode_of_payment()
    create_pos_profile()

    create_so_types()
    create_opd_service_unit()
    create_user_permision()
    translate_gender()
    delate_genders()
    sources_creations()
    roles_creations()
    frappe.db.commit()

    # create_workspace()
    print("*****  Succesfully Created all Setups and Defaults! Alhamdulilaah  ******")
    print("#############################################")
    print("*********** Tommorow is not Just another day! ********")





custom_fields = {
    "Selling Settings": [
        {
            "fieldname": "discount_levels_section",
            "fieldtype": "Section Break",
            "label": "Discount Levels",
            "insert_after": "hide_tax_id",
        },
        {
            "fieldname": "discount_levels",
            "fieldtype": "Table",
            "options": "Discount Level",
            "insert_after": "hide",
        },
    ]
}


def make_custom_fields():
    create_custom_fields(custom_fields, ignore_validate=True)
    frappe.db.commit()



def create_account_for_item_group():

    print("Creating Accounts for item groups")
    for item_group in item_groups:
        if frappe.db.exists("Account", item_group + ' - '+abbr):
            continue
        doc = frappe.get_doc({
            "doctype": "Account",
            "account_name": item_group,
            "company": company,
            "parent_account": "4100 - Direct Income - "+abbr,
        })
        doc.insert()
        frappe.db.commit()
    print("Account Creation Done")

# doc.append("item_group_defaults" , {
#     ...:         "company" : company,
#     ...:        "income_account" : item_group +' - ' + abbr
#     ...:      })


def create_item_groups():
    print("Creating  item groups")
    for item_group in item_groups:
        if frappe.db.exists("Item Group", item_group):
            item_g = frappe.get_doc("Item Group", item_group)

            print("Deleting Exitesting Item Group ", item_g)
            item_g.append("item_group_defaults", {
            "company": company,
            "income_account": item_group + ' - ' + abbr
                })
            # item_g.delete()
            item_g.save()
        else:
            doc = frappe.new_doc("Item Group")
            doc.item_group_name = item_group
            doc.append("item_group_defaults", {
                "company": company,
                "income_account": item_group + ' - ' + abbr
            })

            doc.insert()
            frappe.db.commit()
    print(" Item Group Creation Done")


def create_consultation_item():
    print("Creating Consultation Item")
    if not frappe.db.exists("Item" , "OPD Consultation"):
        doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": "OPD Consultation",
            "item_group": "Consultation",
            "is_stock_item": 0,
            "standard_rate": 10
        })
        doc.insert()
        frappe.db.commit()
        print("Done")


# def create_workspace():
# 	print("Creating Workspaces ")
# 	workspacs = {
# 		"Cashier": [
# 				{"doctype": "Patient", "label": "Patient"},
# 				{"doctype": "Patient Appointment", "label": "OPD"},
# 				{"doctype": "Inpatient Record", "label": "IPD"},
# 				{"doctype": "Sales Invoice", "label": "GP"}

# 		],
# 		"Pharmacy": [

# 			{"doctype": "Patient Appointment", "label": "OPD"},
# 			{"doctype": "Inpatient Record", "label": "IPD"},
# 			{"doctype": "GP", "label": "GP"}

# 		],

# 		"Doctor": [

# 			{"doctype": "Patient Appointment", "label": "OPD"},
# 			{"doctype": "Inpatient Record", "label": "IPD"},
# 			{"doctype": "Lab Test", "label": "Lab Test"},


# 		],
# 		"Nurse": [


# 			{"doctype": "Inpatient Record", "label": "IPD"},



# 		],
# 		"OT": [


# 			{"doctype": "Clinical Procedure", "label": "Clinical Procedure"},


# 		],

# 		"Lab": [


# 			{"doctype": "Lab Test", "label": "Lab Test"}


# 		],
# 		"Imaging": [


# 			{"doctype": "Lab Test", "label": "Lab Test"}


# 		],

# 		"Emergency": [


# 			{"doctype": "Patient Appointment", "label": "OPD"},


# 		],

# 		"Admin": [


# 			{"doctype": "Patient Appointment", "label": "OPD"},


# 		],



# 	}
    
# 	for workspace_name in custom_rol_workpace:
# 		if frappe.db.exists("Workspace", workspace_name):
# 			continue
# 		doc = frappe.new_doc("Workspace")
# 		doc.label = workspace_name
# 		doc.ccategory = "Modules"
# 		doc.disable_user_customization = 1
# 		for short in workspacs[f'{workspace_name}']:
# 			doc.append("shortcuts", {
# 				"type": "DocType",

# 				"link_to": short['doctype'],
# 				"label": short['label']

# 			})
    
# 		doc.insert()
# 		print(workspace_name, " Workspaces Created")
# 	frappe.db.commit()
# 	print("Done")


def create_so_types():
    print("Creating Sales Type ")
    frappe.reload_doc("his", "doctype", "sales_type")

    for so_type in ("Cashiers", "Cashier", "Pharmacy","Opticals"):
        if frappe.db.exists("Sales Type", so_type):
            continue

        doc = frappe.new_doc("Sales Type")
        doc.type = so_type
        doc.insert()

    frappe.db.commit()
    print("Done")


def set_system_setting():
    print("System  Setting ")
    frappe.db.set_single_value('System Settings', 'enable_password_policy', 0)
    frappe.db.set_single_value(
        'System Settings', 'allow_login_using_mobile_number', 1)
    frappe.db.set_single_value(
        'System Settings', 'allow_login_using_user_name', 1)
    
    frappe.db.commit()
    print("Done")


def create_users():
    print("Creating User ")
    for user in custom_rol_workpace:
        # Role Permision Manager
        # 	newdoc = frappe.get_doc({"doctype" : "Custom DocPerm" , "role" :"Cashier" , "parent" : "Sales Order" , "read" : 1 , "select" : 1 , "
        # ...: submit" : 1 , "write" : 1 , "create" : 1 ,  })
        if frappe.db.exists("User", user.replace(" ", "_").lower() + '@testdomain.com'):
            continue
        doc = frappe.new_doc("User")
        doc.email = user.replace(" ", "_").lower() + '@testdomain.com'
        doc.first_name = user
        doc.username = user.lower()
        doc.new_password = "123"

        doc.append('roles', {
            'role': user})
        doc.insert()

        print(user, "User Created ")
    frappe.db.commit()
    print("Done")


def create_user_permision():
    print("Creating user Permisions")
    for user in sales_users:
        if frappe.db.exists({
            "doctype" : "User Permission",
            "allow" : "Sales Type",
            "user" : user.lower() + "@testdomain.com"

        }):
            continue
        doc = frappe.new_doc("User Permission")
        doc.user = user.lower() + "@testdomain.com"
        doc.allow = "Sales Type"
        doc.for_value = user
        doc.is_default = 1
        doc.apply_to_all_doctypes = 1
        doc.insert()
    frappe.db.commit()
    print("Done")


# def create_workspace_permsion():
# 	print("Creating Workspace  Permisions ")
# 	for workspace_rol in custom_rol_workpace:

# 		if frappe.db.exists("Workspace Perms", workspace_rol):
# 			continue
# 		doc = frappe.new_doc("Workspace Perms")
# 		doc.workspace = workspace_rol
# 		doc.append("visible_to_roles", {
# 			"role_name": workspace_rol
# 		})
# 		for role in custom_rol_workpace:
# 			if role != workspace_rol:
# 				doc.append("hidden_to_roles", {
# 					"role_name": role
# 				})
# 		doc.insert()

# 		# for df in table.meta.get('fields'):

# 		# 	table.set(df.fieldname, role)
# 	frappe.db.commit()
# 	print("Done")


def create_cash_accounts():
    print("Creating Cash Accounts")
    for account in ["Cashier", "Pharmacy" , "Main Cashier"]:
        if frappe.db.exists("Account", account +' - '+abbr):
            continue
        doc = frappe.get_doc({
            "doctype": "Account",
            "account_name": account,
            "company": company,
            "account_type": "Cash",
            "parent_account": "1100 - Cash In Hand - "+abbr,
        })
        doc.insert()
    frappe.db.commit()
    print("Done")
def create_his_accounts():
    print("Creating HIS Accounts")
    for account in ["Employee Receivable"]:
        if frappe.db.exists("Account", account +' - '+abbr):
            continue
        doc = frappe.get_doc({
            "doctype": "Account",
            "account_name": account,
            "company": company,
            "account_type": "Payable",
            "parent_account": "1300 - Accounts Receivable - "+abbr,
        })
        doc.insert()
    for account in ["Cashier","Pharmacy"]:
        if frappe.db.exists("Account", account +' - '+abbr):
            continue
        doc = frappe.get_doc({
            "doctype": "Account",
            "account_name": account,
            "company": company,
            "account_type": "Cash",
            "parent_account": "1100 - Cash In Hand - "+abbr,
        })
        doc.insert()
    frappe.db.commit()
    print("Done")


def create_mode_of_payment():
    print("Creating Mode of Payments")
    for account in sales_users:
        # print(account)
        if frappe.db.exists("Mode of Payment", account):
            continue
        doc = frappe.new_doc("Mode of Payment")
        doc.mode_of_payment = account
        doc.type = "Cash"
        doc.append('accounts', {
            "company": company,
            "default_account": account + ' - ' + abbr

        })
        doc.insert()
    frappe.db.commit()
    print("Done")


def create_pos_profile():
    print("Creating POS Profiles")
    for user in sales_users:
        if frappe.db.exists("POS Profile" , user):
            continue
        doc = frappe.new_doc("POS Profile")
        doc.company = company
        doc.name = user
        doc.warehouse = defualt_warehouse
        doc.write_off_account = write_of_account
        doc.write_off_cost_center = cost_center
        doc.append("applicable_for_users", {
            "default": 1,
            "user": user+'@testdomain.com'

        })
        doc.append("payments", {
            "default": 1,
            "mode_of_payment": user

        })
        doc.insert()
    print("Done")


def create_opd_service_unit():
    print("Creating OPD Service Unit")
    if not frappe.db.exists("Healthcare Service Unit Type" ,"OPD Rooms"):
        service_type = frappe.new_doc("Healthcare Service Unit Type")
        service_type.service_unit_type = "OPD Rooms"
        service_type.allow_appointments = 1
        service_type.insert()
        
        service_unit = frappe.new_doc("Healthcare Service Unit")
        service_unit.healthcare_service_unit_name = "OPD Room"
        service_unit.service_unit_type = service_type.name
        service_unit.company = company
        service_unit.parent_healthcare_service_unit = "All Healthcare Service Units " + '- ' + abbr
        service_unit.insert()
    print("Done")


def healthcare_setting():
    print("Setting Up Healthcare ")
    frappe.db.set_single_value(
        'Healthcare Settings', 'patient_name_by', 'Naming Series')
    frappe.db.set_single_value(
        'Healthcare Settings', 'automate_appointment_invoicing', 1)
    frappe.db.set_single_value(
        'Healthcare Settings', 'enable_free_follow_ups', 1)
    frappe.db.set_single_value('Healthcare Settings', 'max_visits', 20)
    frappe.db.set_single_value('Healthcare Settings', 'valid_days', 7)
    frappe.db.set_single_value(
        'Healthcare Settings', 'allow_discharge_despite_unbilled_services', 1)
    frappe.db.set_single_value(
        'Healthcare Settings', 'op_consulting_charge_item', "OPD Consultation")
    frappe.db.set_single_value(
        'Healthcare Settings', 'create_lab_test_on_si_submit', 0)
    frappe.db.commit()
    print("Done")


def selling_setting():
    print("Setting Up Selling ")
    frappe.db.set_single_value(
        'Selling Settings', 'cust_master_name', "Naming Series")
    frappe.db.commit()
    print("Done")


def accounting_setting():
    print("Setting Up Accounting ")
    frappe.db.set_single_value(
        'Accounts Settings', 'enable_discount_accounting', 0)
    frappe.db.set_single_value(
        'Accounts Settings', 'delete_linked_ledger_entries', 1)
    
    frappe.db.set_single_value(
        'Stock Settings', 'valuation_method', "Moving Average")
    
    
    frappe.db.commit()
    print("Done")


def website_setting():
    print("Setting Up Website Setting ")
    frappe.db.set_single_value('Website Settings', 'app_name', company)
    frappe.db.set_single_value('Website Settings', 'disable_signup', 1)
    frappe.db.set_single_value('Website Settings', 'home_page', "login")
    frappe.db.set_single_value('Website Settings', 'copyright', "Rasiin Technology")

    

    frappe.db.commit()
    print("Done")


def make_custom_roles():
    print("Creating Roles ")

    for role_name in custom_rol_workpace:
        if frappe.db.exists("Role", role_name):
            continue
        role = frappe.new_doc("Role")
        role.update({"role_name": role_name, "desk_access": 1})
        try:
            role.save()
        except frappe.DuplicateEntryError:
            pass

    frappe.db.commit()
    print("Done")


def make_property_setters():
    print("Setting Up Naming Series for Patient , Patient Appoint , Healhcare Practitioner and Sample Collection")
    make_property_setter('Patient', "naming_series", "default", '', "Text")
    make_property_setter('Patient', "naming_series", "options", 'PID-', "Text")
    make_property_setter('Patient', "naming_series", "default", 'PID-', "Text")
    make_property_setter('Patient Appointment', "naming_series", "default", '', "Text")
    make_property_setter('Patient Appointment',"naming_series", "options", 'OPD-', "Text")
    make_property_setter('Patient Appointment', "naming_series", "default", 'OPD-', "Text")
    make_property_setter('Healthcare Practitioner', "","autoname", "field:first_name", "Data", True)
    make_property_setter('Sample Collection', "sample", "reqd", 0, "Check")
    
    

    frappe.db.commit()
    print("Done")


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
        if frappe.db.exists("Gender" ,i):
            del_genders = frappe.get_doc("Gender" , i)
            del_genders.delete()
            frappe.db.commit()

def accounts_creations():
   
    for i in ["Discount", "Free Que"]:
        if not frappe.db.exists("Account" ,i+' - '+abbr):
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
    if not frappe.db.exists("Mode of Payment" ,"Free"):
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
    for i in ["IPD","OPD","WP","E.R", "PACKAGE", "Que"]:
         if not frappe.db.exists("Source Order" ,i):
            
            source_creation = frappe.get_doc({
                "doctype" : "Source Order",
                "source" : i
            })
    
            source_creation.save()
            frappe.db.commit()   

def roles_creations():
    for i in ["Tafaariiq"]:
         if not frappe.db.exists("Role" ,i):
            role_creation = frappe.get_doc({
                "doctype" : "Role",
                "role_name" : i
            })
    
            role_creation.save()
            frappe.db.commit()
 

def uom_creations():
    for i in ["Strep"]:
        if not frappe.db.exists("UOM" ,i):
            uom_creation = frappe.get_doc({
                "doctype" : "UOM",
                "uom_name" : i,
                "must_be_whole_number" : 0
            })
    
            uom_creation.save()
            frappe.db.commit()
