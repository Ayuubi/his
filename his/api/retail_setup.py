# import frappe

# from erpnext.stock.doctype.item.item import Item

# class CustomItem(Item):
#     def add_default_uom_in_conversion_factor_table(self):
#         if not self.is_new() and self.has_value_changed("stock_uom"):
#             self.uoms = []
#             frappe.msgprint(
#                  ("Successfully changed Stock UOM, please redefine conversion factors for new UOM."),
#                  alert=True
#                  )
#         uoms_list = [d.uom for d in self.get("uoms")]
#         if self.stock_uom not in uoms_list:
#             self.append("uoms", {"uom": self.stock_uom, "conversion_factor": 1})
#         if "Strep" not in uoms_list and self.strep:
#             self.append("uoms", {"uom": "Strep", "conversion_factor": 1})





# @frappe.whitelist()
# def purchase_invoice_retail(doc , method = None):
#     retail_setup = frappe.get_doc("Retail Setup", "Retail Setup")
#     if retail_setup.allow_retail:

#         if doc.items:
#             for item in doc.items:
#                 item_doc = frappe.get_doc("Item" , item.item_code)
#                 if item.streps and item_doc.strep:
                    
#                     item_doc.uoms[1].conversion_factor = 1/float(item.streps)
#                     item_doc.uoms[1].no_of_streps = float(item.streps)
#                     item_doc.save()  


# @frappe.whitelist()
# def stock_reconciliation_retail(doc, method = None):
#     retail_setup = frappe.get_doc("Retail Setup", "Retail Setup")
#     if retail_setup.allow_retail:
#         if doc.items:
#             for item in doc.items:
#                 # item_gr = frappe.db.get_value("Item" , item.item_code , "item_group")
#                 item_doc = frappe.get_doc("Item" , item.item_code)
#                 if item.strips   and item_doc.strep:
#                     item_doc.uoms[1].conversion_factor = 1/float(item.strips)
#                     item_doc.uoms[1].no_of_streps = float(item.strips)
#                     item_doc.save()
#                 # if not item.strips and item.item_group == "Strip":
#                 #     new_doc = frappe.get_doc({
#                 #         "doctype" : "Missing Strip Items",
#                 #         "item" : item.item_code,
#                 #         "qty" :  item.qty,
#                 #         "strips" : item.strips
#                 #     })
#                 #     new_doc.save() 

# # @frappe.whitelist()
# # def sales_invoice_retail(doc, method = None):
# #     retail_setup = frappe.get_doc("Retail Setup", "Retail Setup")
# #     if retail_setup.allow_retail:

# #         if doc.items:
# #              for item in doc.items:
# #                 if item.rate <= 0:
# #                     frappe.throw(f"Rate can not be zero for <h6>{item.item_code}<h6/>")



# # @frappe.whitelist()
# # def stock_entry_retail(doc, method = None):
# #     retail_setup = frappe.get_doc("Retail Setup", "Retail Setup")
# #     if retail_setup.allow_retail:
# #         if doc.items:
# #             for item in doc.items:
# #                 if item.strips and item.strips:
# #                     item_doc = frappe.get_doc("Item" , item.item_code)
                    
# #                     item_doc.uoms[1].conversion_factor = 1/float(item.strips)
# #                     item_doc.uoms[1].no_of_streps = float(item.strips)
# #                     item_doc.save()
# #                 if not item.strips and item.item_group == "Strip":
# #                     new_doc = frappe.get_doc({
# #                     "doctype" : "Missing Strip Items",
# #                     "item" : item.item_code,
# #                     "qty" :  item.qty,
# #                     "strip" : item.strips
# #                     })
# #                     new_doc.save()
