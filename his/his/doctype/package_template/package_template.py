import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.rename_doc import rename_doc
from frappe.utils import flt


class PackageTemplate(Document):
    def after_insert(self):
        if not self.item:
            create_item_from_template(self)

    def validate(self):
        # ✅ ALWAYS compute total rate first (server-side)
        old_rate = flt(self.get_db_value("rate")) if not self.is_new() else 0.0
        self.set_total_rate_from_prescription()

        # ✅ If total changed, force updating Item + Item Price on save
        if not self.is_new() and flt(self.rate) != old_rate:
            self.change_in_item = 1

        if self.is_billable and (not self.rate or flt(self.rate) <= 0.0):
            frappe.throw(_("Standard Selling Rate should be greater than zero."))

        self.enable_disable_item()

    def set_total_rate_from_prescription(self):
        total = 0.0
        for row in (self.get("package_prescription") or []):
            total += flt(row.rate) * flt(row.qty)
        self.rate = flt(total)

    def on_update(self):
        # Update Item + Item Price whenever change_in_item is set
        if self.change_in_item and self.is_billable and self.item:
            self.update_item()

            price_list_name = (
                frappe.db.get_value("Selling Settings", None, "selling_price_list")
                or frappe.db.get_value("Price List", {"selling": 1}, "name")
            )

            # ✅ Find existing item price for this Item + price list
            item_price_name = self.item_price_exists(price_list_name)

            if item_price_name:
                frappe.db.set_value("Item Price", item_price_name, "price_list_rate", flt(self.rate))
            else:
                # ✅ Create Item Price using self.item (not template_code)
                make_item_price(self.item, price_list_name, flt(self.rate))

            self.db_set("change_in_item", 0)

        elif not self.is_billable and self.item:
            frappe.db.set_value("Item", self.item, "disabled", 1)

        self.reload()

    def on_trash(self):
        # Remove template reference from item and disable item
        if self.item:
            try:
                item = self.item
                self.db_set("item", "")
                frappe.delete_doc("Item", item)
            except Exception:
                frappe.throw(_("Not permitted. Please disable the Package Template"))

    def enable_disable_item(self):
        if self.is_billable and self.item:
            frappe.db.set_value("Item", self.item, "disabled", 1 if self.disabled else 0)

    def update_item(self):
        item = frappe.get_doc("Item", self.item)
        if item:
            item.update({
                "item_name": self.template,
                "item_group": self.item_group,
                "disabled": 0,
                "standard_rate": flt(self.rate),
                "description": self.description
            })
            item.flags.ignore_mandatory = True
            item.save(ignore_permissions=True)

    def item_price_exists(self, price_list_name):
        # ✅ Correct lookup: Item Price is based on item_code = Item.name, and price_list
        return frappe.db.get_value(
            "Item Price",
            {"item_code": self.item, "price_list": price_list_name},
            "name"
        )


def create_item_from_template(doc):
    uom = frappe.db.exists("UOM", "Unit") or frappe.db.get_single_value("Stock Settings", "stock_uom")

    # Insert item
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": doc.template_code,
        "item_name": doc.template,
        "item_group": doc.item_group,
        "description": doc.description,
        "is_sales_item": 1,
        "is_service_item": 1,
        "is_purchase_item": 0,
        "is_stock_item": 0,
        "include_item_in_manufacturing": 0,
        "show_in_website": 0,
        "is_pro_applicable": 0,
        "disabled": 0 if doc.is_billable and not doc.disabled else doc.disabled,
        "stock_uom": uom
    }).insert(ignore_permissions=True, ignore_mandatory=True)

    # Insert item price
    if doc.is_billable:
        price_list_name = (
            frappe.db.get_value("Selling Settings", None, "selling_price_list")
            or frappe.db.get_value("Price List", {"selling": 1}, "name")
        )
        make_item_price(item.name, price_list_name, flt(doc.rate))

    # Set item in the template
    frappe.db.set_value("Package Template", doc.name, "item", item.name)

    doc.reload()


def make_item_price(item, price_list_name, item_price):
    frappe.get_doc({
        "doctype": "Item Price",
        "price_list": price_list_name,
        "item_code": item,
        "price_list_rate": flt(item_price)
    }).insert(ignore_permissions=True, ignore_mandatory=True)


@frappe.whitelist()
def change_test_code_from_template(template_code, doc):
    doc = frappe._dict(json.loads(doc))

    if frappe.db.exists({"doctype": "Item", "item_code": template_code}):
        frappe.throw(_("Package Item {0} already exist").format(template_code))
    else:
        rename_doc("Item", doc.name, template_code, ignore_permissions=True)
        frappe.db.set_value("Package Template", doc.name, "template_code", template_code)
        frappe.db.set_value("Package Template", doc.name, "template", template_code)
        rename_doc("Package Template", doc.name, template_code, ignore_permissions=True)

    return template_code


# import json
# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.model.rename_doc import rename_doc
# from frappe.utils import flt

# class PackageTemplate(Document):
#     def after_insert(self):
#         if not self.item:
#             create_item_from_template(self)

#     def validate(self):
#         # ✅ ALWAYS compute total rate first (server-side)
#         self.set_total_rate_from_prescription()

#         if self.is_billable and (not self.rate or self.rate <= 0.0):
#             frappe.throw(_('Standard Selling Rate should be greater than zero.'))

#         # self.validate_conversion_factor()
#         self.enable_disable_item()
    
#     def set_total_rate_from_prescription(self):
#         total = 0.0
#         for row in (self.get("package_prescription") or []):
#             total += flt(row.rate) * flt(row.qty)
#         self.rate = flt(total)

#     def on_update(self):
#         # If change_in_item update Item and Price List
#         if self.change_in_item and self.is_billable and self.item:
#             self.update_item()
#             item_price = self.item_price_exists()
#             if not item_price:
#                 if self.rate and self.rate > 0.0:
#                     price_list_name = frappe.db.get_value('Selling Settings', None, 'selling_price_list') or frappe.db.get_value('Price List', {'selling': 1})
#                     make_item_price(self.template_code, price_list_name, self.rate)
#             else:
#                 frappe.db.set_value('Item Price', item_price, 'price_list_rate', self.rate)

#             self.db_set('change_in_item', 0)

#         elif not self.is_billable and self.item:
#             frappe.db.set_value('Item', self.item, 'disabled', 1)

#         self.reload()

#     def on_trash(self):
#         # Remove template reference from item and disable item
#         if self.item:
#             try:
#                 item = self.item
#                 self.db_set('item', '')
#                 frappe.delete_doc('Item', item)
#             except Exception:
#                 frappe.throw(_('Not permitted. Please disable the Package Template'))

#     def enable_disable_item(self):
#         if self.is_billable:
#             if self.disabled:
#                 frappe.db.set_value('Item', self.item, 'disabled', 1)
#             else:
#                 frappe.db.set_value('Item', self.item, 'disabled', 0)

#     def update_item(self):
#         item = frappe.get_doc('Item', self.item)
#         if item:
#             item.update({
#                 'item_name': self.template,
#                 'item_group': self.item_group,
#                 'disabled': 0,
#                 'standard_rate': self.rate,
#                 'description': self.description
#             })
#             item.flags.ignore_mandatory = True
#             item.save(ignore_permissions=True)

#     def item_price_exists(self):
#         item_price = frappe.db.exists({'doctype': 'Item Price', 'item_code': self.template_code})
#         if item_price:
#             return item_price[0][0]
#         return False

#     # def validate_conversion_factor(self):
#     # 	if self.lab_test_template_type == 'Single' and self.secondary_uom and not self.conversion_factor:
#     # 		frappe.throw(_('Conversion Factor is mandatory'))
#     # 	if self.lab_test_template_type == 'Compound':
#     # 		for item in self.normal_test_templates:
#     # 			if item.secondary_uom and not item.conversion_factor:
#     # 				frappe.throw(_('Row #{0}: Conversion Factor is mandatory').format(item.idx))
#     # 	if self.lab_test_template_type == 'Grouped':
#     # 		for group in self.item_groups:
#     # 			if group.template_or_new_line == 'Add New Line' and group.secondary_uom and not group.conversion_factor:
#     # 				frappe.throw(_('Row #{0}: Conversion Factor is mandatory').format(group.idx))


# def create_item_from_template(doc):
#     uom = frappe.db.exists('UOM', 'Unit') or frappe.db.get_single_value('Stock Settings', 'stock_uom')
#     # Insert item
#     item =  frappe.get_doc({
#         'doctype': 'Item',
#         'item_code': doc.template_code,
#         'item_name':doc.template,
#         'item_group': doc.item_group,
#         'description':doc.description,
#         'is_sales_item': 1,
#         'is_service_item': 1,
#         'is_purchase_item': 0,
#         'is_stock_item': 0,
#         'include_item_in_manufacturing': 0,
#         'show_in_website': 0,
#         'is_pro_applicable': 0,
#         'disabled': 0 if doc.is_billable and not doc.disabled else doc.disabled,
#         'stock_uom': uom
#     }).insert(ignore_permissions=True, ignore_mandatory=True)

#     # Insert item price
#     if doc.is_billable and doc.rate != 0.0:
#         price_list_name = frappe.db.get_value('Selling Settings', None, 'selling_price_list') or frappe.db.get_value('Price List', {'selling': 1})
#         if doc.rate:
#             make_item_price(item.name, price_list_name, doc.rate)
#         else:
#             make_item_price(item.name, price_list_name, 0.0)
#     # Set item in the template
#     frappe.db.set_value('Package Template', doc.name, 'item', item.name)

#     doc.reload()

# def make_item_price(item, price_list_name, item_price):
#     frappe.get_doc({
#         'doctype': 'Item Price',
#         'price_list': price_list_name,
#         'item_code': item,
#         'price_list_rate': item_price
#     }).insert(ignore_permissions=True, ignore_mandatory=True)

# @frappe.whitelist()
# def change_test_code_from_template(template_code, doc):
#     doc = frappe._dict(json.loads(doc))

#     if frappe.db.exists({'doctype': 'Item', 'item_code': template_code}):
#         frappe.throw(_('Package Item {0} already exist').format(template_code))
#     else:
#         rename_doc('Item', doc.name, template_code, ignore_permissions=True)
#         frappe.db.set_value('Package Template', doc.name, 'template_code', template_code)
#         frappe.db.set_value('Package Template', doc.name, 'template', template_code)
#         rename_doc('Package Template', doc.name, template_code, ignore_permissions=True)
#     return template_code
