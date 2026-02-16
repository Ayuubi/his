import base64, re, frappe
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def save_image_to_child(parent_doctype, parent_name, child_doctype, child_name, fieldname, data_url):
    """
    data_url: "data:image/png;base64,....."
    Saves as File and sets the Attach field on the child row. Returns file_url.
    """
    m = re.match(r'^data:(.*?);base64,(.*)$', data_url)
    if not m:
        frappe.throw('Invalid data URL')
    mimetype, b64 = m.groups()
    ext = 'png' if 'png' in mimetype else 'jpg'
    file_name = f"{child_name}-{fieldname}.{ext}"
    content = base64.b64decode(b64)
    # frappe.errprint(file_name + " " + " "+ parent_doctype + " "+ parent_name + "Child "+ child_doctype)
    # frappe.errprint(fieldname)
    file_doc = save_file(file_name, content, parent_doctype, parent_name, is_private=0)
    frappe.db.set_value(child_doctype, child_name, fieldname, file_doc.file_url)
    return file_doc.file_url




# # your_app/api.py
# import base64
# import frappe
# from frappe.utils.file_manager import save_file

# @frappe.whitelist()
# def save_biometrics(doctype, docname, sig_image_b64=None, sig_hex=None,
#                     fingerprint_png_b64=None, fp_template_b64=None):
#     doc = frappe.get_doc(doctype, docname)

#     # Save the signature image (base64 PNG)
#     if sig_image_b64:
#         b64 = sig_image_b64.split(',')[-1]
#         f = save_file(f"{docname}-signature.png", base64.b64decode(b64),
#                       doctype, docname, is_private=1)
#         # Optionally store file URL on a field
#         if hasattr(doc, "signature_image"):
#             doc.db_set("signature_image", f.file_url)

#     # Save the .sig file (biometric signature)
#     if sig_hex:
#         sig_bytes = bytes.fromhex(sig_hex)
#         save_file(f"{docname}.sig", sig_bytes, doctype, docname, is_private=1)

#     # Save the fingerprint image (base64 PNG)
#     if fingerprint_png_b64:
#         b64 = fingerprint_png_b64.split(',')[-1]
#         # Decoding base64 string into binary
#         decoded_data = base64.b64decode(b64)
#         # Save the file and get the file URL
#         f = save_file(f"{docname}-fingerprint.png", decoded_data, doctype, docname, is_private=1)
#         # Store the file URL in the fingerprint_image field
#         frappe.db.set_value(doctype, docname, "fingerprint_image", f.file_url)

#         # Save the fingerprint template (base64) in the Long Text field
#         if fp_template_b64:
#             # Store the base64 string as it is in the fingerprint_template field
#             frappe.db.set_value(doctype, docname, "fingerprint_template", fp_template_b64)

#     return {"ok": True}

