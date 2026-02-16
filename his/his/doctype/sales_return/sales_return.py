# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe
from his.api.create_inv import create_inv
from frappe.model.document import Document

class SalesReturn(Document):
    def on_submit(self):
        retail_setup = frappe.get_doc("Retail Setup", "Retail Setup")
        if retail_setup.allow_retail:
            if self.items:
                for item in self.items:
                    item_doc = frappe.get_doc("Item" , item.item_code)
                    if item.streps and item_doc.strep:
                        
                        item_doc.uoms[1].conversion_factor = 1/float(item.streps)
                        item_doc.uoms[1].no_of_streps = float(item.streps)
                        item_doc.save() 
        # frappe.msgprint("ok")
        sales_doc = create_inv(self.name ,dt = 'Sales Return' , is_sales_return = True)
        self.sales_invoice = sales_doc.name
        self.save()
    def on_cancel(self):
        if self.sales_invoice:
            sales_doc = frappe.get_doc("Sales Invoice" , self.sales_invoice)
            sales_doc.cancel()


@frappe.whitelist()
def get_billed_items(patient, from_date, to_date):
    list_of_bills = frappe.db.get_list("Sales Invoice",
                                        filters={"patient": patient,
                                                 "docstatus": 1,
                                                #  "is_return": 0,
                                                 "posting_date": ['between', [from_date, to_date]]},
                                        pluck="name")

    # Fetch all items for the invoices in list_of_bills
    items_of_bills = frappe.db.get_all("Sales Invoice Item",
                                         filters={"parent": ["in", list_of_bills]},
                                         fields=["item_code", "qty", "rate", "item_name", "description", "warehouse", "uom"])

    stock_items = {}
    for item in items_of_bills:
        item_code = item['item_code']
        qty = item['qty']
        rate = item['rate']
        item_name = item['item_name']
        description = item['description']
        warehouse = item['warehouse']
        uom= item['uom']

        is_stock_item = frappe.db.get_value("Item", {"item_code": item_code}, "is_stock_item")
        if is_stock_item:
            if item_code in stock_items:
                stock_items[item_code]['qty'] += qty
                # You can choose how to handle rate, item_name, description, warehouse
                # Here, I'm keeping the first entry for simplicity
                stock_items[item_code]['rate'] = rate  # You might want to store the first rate or calculate an average
                stock_items[item_code]['item_name'] = item_name
                stock_items[item_code]['description'] = description
                stock_items[item_code]['warehouse'] = warehouse
                stock_items[item_code]['uom'] = uom
            else:
                stock_items[item_code] = {
                    "item_code": item_code,
                    "qty": qty,
                    "rate": rate,
                    "item_name": item_name,
                    "description": description,
                    "warehouse": warehouse,
                    "uom": uom
                }

    # Convert the dictionary to a list of stock items
    stock_items_list = list(stock_items.values())

    # Now stock_items_list contains the summed quantities and additional details for each stock item
    # frappe.errprint(stock_items_list)

    return stock_items_list  # Return the stock items list
