import frappe
import json
from erpnext.stock.get_item_details import get_pos_profile
@frappe.whitelist()
def create_inv(doc_name ,dt , is_sales_return = False ,  is_credit = False):
    cash_sales = frappe.get_doc(dt , doc_name)
    source = ''
    if dt == "Walking Patient":
        if cash_sales.paid_amount == 0:
            is_credit = True
        source = "WP"
    else:
        source = cash_sales.source_order
    
    pos_profile = get_pos_profile(cash_sales.company)
    mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
    default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
    
    customer = cash_sales.customer
    items = []
    empty_items = ""
    cost_center = cash_sales.cost_center
    for item in cash_sales.items:

        qty = item.qty
        if is_sales_return:
            qty = float(item.qty) * (-1)
        items.append({
            "item_code" : item.item_code,
            "rate" : item.rate,
            "qty" : qty,
            "uom" : item.uom,
            # "warehouse": item.warehouse
            # "batch_no" : item.batch_no
            "cost_center" : cost_center
        })
    payments = []
    paid_amount = 0
    if not is_sales_return:
        paid_amount = cash_sales.paid_amount
    is_pos = 0
    account = ''
    if is_sales_return and cash_sales.refund == 1:
        is_pos = 1
        paid_amount = cash_sales.grand_total * (-1)
        payments.append(
                {
                    "mode_of_payment" : mode_of_payment,
                    "amount" : paid_amount
                    
                }
            )
        
        
 
        
    
    
    if not is_credit and not is_sales_return :
        is_pos = 1
        payments.append(
                {
                    "mode_of_payment" : mode_of_payment,
                    "amount" : paid_amount
                    
                }
            )

    is_return = 0
    # frappe.errprint(payments)
    if is_sales_return :
         is_return = 1 
    sales_doc = frappe.get_doc({
        "doctype" : "Sales Invoice",
        "is_return" : is_return,
        "posting_date" : cash_sales.transaction_date,
        "customer": customer,
        "patient" : cash_sales.patient,
        "is_pos" : 0,
        "discount_amount" : cash_sales.discount_amount,
        "payments": payments,
        "cost_center": cash_sales.cost_center,
        "so_type": cash_sales.so_type,
        "voucher_no" : cash_sales.name,
        "source_order" : source,
        "ref_practitioner" : cash_sales.ref_practitioner,
        "additional_discount_percentage": cash_sales.additional_discount_percentage,
        "items" : items,
        "paid_amount" : paid_amount,
       
    })
    # frappe.errprint(sales_doc.as_dict())
    sales_doc.insert()
    sales_doc.submit()
    frappe.msgprint('Billed successfully')
    return sales_doc



def purchase(doc_name ,dt , is_purchase_return = False , is_credit = False):
    cash_sales = frappe.get_doc(dt , doc_name)
    supplier = cash_sales.supplier
    # frappe.msgprint(order_doc.name)
    items = []
    empty_items = ""
    for item in cash_sales.items:

        qty = item.qty
        if is_purchase_return:
            qty = float(item.qty) * (-1)
        items.append({
            "item_code" : item.item_code,
            "rate" : item.rate,
            "qty" : qty
        })
    payments = []

    
    paid_amount = cash_sales.grand_total
    is_paid = 0
    account = ''
    if is_purchase_return and cash_sales.refund == 1:
        is_paid = 1
        account = cash_sales.account
        paid_amount = cash_sales.grand_total * (-1)

    
    if not is_credit and not is_purchase_return :
        is_paid = 1
        account = cash_sales.account
     
    is_return = 0
    if is_purchase_return :
         is_return = 1 
    frappe.msgprint(str(cash_sales.date))
    pur_doc = frappe.get_doc({
        "doctype" : "Purchase Invoice",
        "posting_date" : cash_sales.date,
        "is_return" : is_return,
        "supplier": supplier,
        "discount_amount" : cash_sales.discount,
        "is_paid" : is_paid,
        "discount_amount" : cash_sales.discount,
        "cash_bank_account" : account,
        "paid_amount" : paid_amount,
        "bill_no" : cash_sales.supplier_invoice,
        # "payments": payments,
        "voucher_no" : cash_sales.voucher_no,
       
        "items" : items,
       
    })
   
    pur_doc.save()
    pur_doc.submit()
    frappe.msgprint('Billed successfully')
    return pur_doc

    
@frappe.whitelist()
def create_inv_refund(doc_name ,dt, que , is_sales_return = False ,  is_credit = False):
    cash_sales = frappe.get_doc(dt , doc_name)
    pos_profile = get_pos_profile(cash_sales.company)
    mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
    default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
  
 
    items = []
    empty_items = ""
    for item in cash_sales.items:

        qty = item.qty
        if is_sales_return:
            qty = float(item.qty) * (-1)
        items.append({
            "item_code" : item.item_code,
            "rate" : item.rate,
            "qty" : qty
        })
    payments = []

    
    paid_amount = cash_sales.grand_total
    is_pos = 0
    account = ''
    if is_sales_return:
        is_pos = 1
        paid_amount = cash_sales.grand_total * (-1)
        payments.append(
                {
                    "mode_of_payment" : mode_of_payment,
                    "amount" : paid_amount
                    
                }
            )
        
        
 
        
    
    
    if not is_credit and not is_sales_return :
        is_pos = 1
        payments.append(
                {
                    "mode_of_payment" : mode_of_payment,
                    "amount" : paid_amount
                    
                }
            )

    is_return = 0
    if is_sales_return :
         is_return = 1 
    sales_doc = frappe.get_doc({
        "doctype" : "Sales Invoice",
        "is_return" : is_return,
        "posting_date" : cash_sales.posting_date,
        "customer": cash_sales.customer,
        "patient" : cash_sales.patient,
        "is_pos" : is_pos,
        "discount_amount" : cash_sales.discount_amount,
        "payments": payments,
        "voucher_no" : cash_sales.name,
        "items" : items,
       
    })
   
    sales_doc.insert(ignore_permissions = True)
    sales_doc.submit()
    frappe.db.set_value('Que', que , 'status', 'Refunded')
    # frappe.msgprint('Refunded successfully')
    return sales_doc


