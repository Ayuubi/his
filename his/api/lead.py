import frappe

@frappe.whitelist(allow_guest=True)
def create_new_lead(full_name, mobile_number, district, sex, age=None):
    try:
        doc = frappe.new_doc("Lead")
        
        # Name fields
        doc.lead_name = full_name
       
        
        # Contact & Personal Info
        doc.mobile_no = mobile_number
        doc.district = district 
        doc.gender = sex    
        
        # if age:
        #     doc.age = age 

        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Lead Form Error: {str(e)}", "Web Form Error")
        frappe.throw("Cilad ayaa dhacday: " + str(e))