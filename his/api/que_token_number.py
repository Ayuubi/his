from erpnext.stock.get_item_details import get_pos_profile
import  frappe

@frappe.whitelist()
def token_numebr(doc, method=None):
    frappe.db.commit()  # Only if needed in your context
    b = frappe.db.sql(
        """
        SELECT MAX(token_no) as max 
        FROM `tabQue` 
        WHERE date = %s AND practitioner = %s
        FOR UPDATE
        """, (doc.date, doc.practitioner), as_dict=True
    )
    num = b[0]['max']
    if num is None:
        num = 0
    doc.token_no = int(num) + 1
