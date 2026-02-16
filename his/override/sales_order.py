from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
import frappe

class CustomSalesOrder(SalesOrder):
    def on_submit(self):
            # self.check_credit_limit()
            self.update_reserved_qty()

            frappe.get_doc("Authorization Control").validate_approving_authority(
                self.doctype, self.company, self.base_grand_total, self
            )
            self.update_project()
            self.update_prevdoc_status("submit")

            self.update_blanket_order()

