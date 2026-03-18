import frappe

@frappe.whitelist(allow_guest=True)
def create_feedback_issue(message_type, department, details, phone_number=None):
    try:
        subject_line = f"[{message_type}] - {department}"
        
        # The phone number is safely stored here in the description
        # formatted_description = f"""
        # **Nooca Fariinta:** {message_type}
        # **Qeybta:** {department}
        # **Telefoonka:** {phone_number if phone_number else 'Lama reebin'}
        
        # **Faahfaahinta:**
        # {details}
        # """

        doc = frappe.new_doc("Issue")
        doc.subject = subject_line
        doc.description = details
        doc.status = "Open"
        doc.qeybta_aad_ka_cabaneyso = department
        doc.mobile_number = {phone_number if phone_number else 'Lama reebin'}
        
        # We removed doc.raised_by = phone_number to prevent the Email validation error
        
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Failed to create Feedback Issue: {str(e)}", "Cabasho Form Error")
        # Removing the generic throw and returning the actual error string can help with debugging
        frappe.throw(str(e))