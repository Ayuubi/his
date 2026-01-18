from __future__ import unicode_literals
import frappe
import json
from frappe.utils import (
    today,
    format_time,
    global_date_format,
    now,
    get_first_day,
)
from frappe.utils.pdf import get_pdf
from frappe import _
from frappe.www import printview
import datetime
from frappe import publish_progress
from frappe.utils.background_jobs import enqueue as enqueue_frappe
from frappe.core.doctype.communication.email import make
from erpnext.accounts.utils import get_balance_on
from frappe.utils import getdate
# import xlsxwriter
from frappe.utils.file_manager import save_file
from io import BytesIO
from frappe.utils import formatdate


@frappe.whitelist()
def get_recipient_list():
    return frappe.db.sql(
        """SELECT
								customer,
								contact,
								email_id,
								MIN(priority) AS priority,
								send_statement
							FROM
								(SELECT
									tab_cus.name AS 'customer',
									tab_con.name AS 'contact',
									tab_con.email_id,
									CASE WHEN is_customer_statement_contact = 1 THEN 1 WHEN tab_con.is_primary_contact = 1 THEN 2 ELSE 3 END AS 'priority',
									CASE WHEN tab_cus.disable_customer_statements = 1 THEN 'No (Disabled for this customer)' WHEN ISNULL(tab_con.email_id) OR tab_con.email_id = '' THEN 'No (No email address on record)' ELSE 'Yes' END AS 'send_statement'
								FROM `tabCustomer` AS tab_cus
									LEFT JOIN `tabDynamic Link` as tab_dyn ON tab_dyn.link_name = tab_cus.name AND tab_dyn.link_doctype = 'Customer' AND tab_dyn.parenttype = 'Contact'
									LEFT JOIN `tabContact` as tab_con ON tab_dyn.parent = tab_con.name
								WHERE tab_cus.disabled = 0) AS t_contacts
							GROUP BY customer
							ORDER BY customer""",
        as_dict=True,
    )


@frappe.whitelist()
def statements_sender_scheduler(manual=None):
    if manual:
        send_statements(manual=manual)
    else:
        enqueue()


def send_statements(company=None, manual=None):
    """
    Send out customer statements
    """
    show_progress = manual
    progress_title = _("Sending customer statements...")

    if show_progress:
        publish_progress(percent=0, title=progress_title)

    if company is None:
        company = frappe.db.get_single_value("Customer Statements Sender", "company")
        if not company:
            frappe.throw(_("Company field is required on Customer Statements Sender"))
            exit()

    from_date_for_all_customers = frappe.db.get_single_value(
        "Customer Statements Sender", "from_date_for_all_customers"
    )
    to_date_for_all_customers = frappe.db.get_single_value(
        "Customer Statements Sender", "to_date_for_all_customers"
    )

    email_list = get_recipient_list()
    idx = 0
    total = len(email_list)
    for row in email_list:
        idx += 1
        if row.email_id is not None and row.email_id != "":
            if row.send_statement == "Yes":
                if show_progress:
                    publish_progress(
                        percent=(idx / total * 100),
                        title=progress_title,
                        description=" Creating PDF for {0}".format(row.customer),
                    )
                send_individual_statement(
                    row.customer,
                    row.email_id,
                    company,
                    from_date_for_all_customers,
                    to_date_for_all_customers,
                )

    if show_progress:
        publish_progress(percent=100, title=progress_title)
        frappe.msgprint("Emails queued for sending")

@frappe.whitelist()
def get_summary_statement(company, customer, from_date, to_date):
    # Normalize customer into a list if needed
    if isinstance(customer, str):
        try:
            customer = frappe.parse_json(customer)
        except Exception:
            customer = [customer]  # Wrap in list if it's just a string

    filters = {
        "company": company,
        "party": customer,
        "from_date": from_date,
        "to_date": to_date
    }

    # customer_name = frappe.db.get_value("Customer", customer[0], "customer_name","patient")
    customer_name, patient_id = frappe.db.get_value("Customer", customer[0], ["customer_name", "patient"])
    currency = frappe.db.get_value("Company", company, "default_currency")
    date_time = frappe.utils.format_datetime(frappe.utils.now_datetime())

    report_doc = frappe.get_doc("Report", "Customer Statement Summary")
    columns, data = report_doc.get_data(
        limit=1000, user="Administrator", filters=filters, as_dict=True
    )

    html = frappe.render_template("his/templates/report/customer_statement_summary_template.html", {
        "title": "Customer Statement Summary",
        "columns": columns,
        "data": data,
        "filters": filters,
        "now": date_time,
        "currency": currency,
        "customer_name": customer_name,
        "patient": patient_id,
        "from": from_date,
        "to": to_date,
    })

    return html



def enqueue():
    """Add method `send_statements` to the queue."""
    enqueue_frappe(
        method=send_statements,
        queue="long",
        timeout=600000,
        is_async=True,
        job_name="send_statments",
    )
@frappe.whitelist()
def download_excel_report(company, customer, cost_center=None, account=None, from_date=None, to_date=None):
    return []
    # cust_doc = frappe.get_doc("Customer", customer)
    # settings_doc = frappe.get_single("Customer Statements Sender")

    # # Default values if from_date or to_date are not provided
    # if not from_date:
    #     from_date = get_first_day(today()).strftime("%Y-%m-%d")
    # if not to_date:
    #     to_date = today()

    # # Get General Ledger report content
    # report_gl = frappe.get_doc("Report", "General Ledger")
    # filters = {
    #     "company": company,
    #     "party_type": "Customer",
    #     "party": [customer],
    #     "from_date": from_date,
    #     "to_date": to_date,
    #     "group_by": "Group by Voucher (Consolidated)",
    # }
    # if account:
    #     filters["account"] = [account]
    # if cost_center:
    #     filters["cost_center"] = [cost_center]

    # columns, data = report_gl.get_data(
    #     limit=500, user="Administrator", filters=filters, as_dict=True
    # )

    # # Add serial numbers as in the HTML report
    # columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    # for i in range(len(data)):
    #     data[i]["idx"] = i + 1

    # # Get the "Beginning" balance from the first transaction (dynamic)
    # beginning_balance = data[0].get("balance", 0) if data else 0  # Set to 0 if no data

    # # Initialize totals for Debit and Credit
    # total_debit = data[-1].get("debit", 0) if data else 0
    # total_credit = data[-1].get("credit", 0) if data else 0

    # # Write to Excel using xlsxwriter
    # output = BytesIO()
    # workbook = xlsxwriter.Workbook(output)
    # worksheet = workbook.add_worksheet("Customer Statement")

    # # Formatting: Bold headers and center title
    # bold_format = workbook.add_format({'bold': True})
    # center_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})

    # # Customer Information (Header)
    # worksheet.merge_range(0, 0, 0, 8, "Customer Statement", center_format)
    # worksheet.write(1, 0, "Customer ID", bold_format)
    # worksheet.write(1, 1, customer)  # Replace with dynamic value
    # worksheet.write(1, 2, "Date From", bold_format)
    # worksheet.write(1, 3, from_date)
    # worksheet.write(2, 0, "Customer Name", bold_format)
    # worksheet.write(2, 1, cust_doc.customer_name)
    # worksheet.write(2, 2, "Date To", bold_format)
    # worksheet.write(2, 3, to_date)

    # # Financial Summary - Using dynamic "Beginning" balance
    # worksheet.write(4, 0, "Beginning", bold_format)
    # worksheet.write(4, 1, beginning_balance)  # Dynamically set the beginning balance
    # worksheet.write(4, 2, "Total Debit", bold_format)
    # worksheet.write(4, 3, total_debit)  # Dynamic Total Debit
    # worksheet.write(4, 4, "Total Credit", bold_format)
    # worksheet.write(4, 5, total_credit)  # Dynamic Total Credit
    # worksheet.write(4, 6, "Total Balance", bold_format)
    # worksheet.write(4, 7, data[-1].get("balance", 0) if data else 0)  # Dynamic Total Balance

    # # Table Headers
    # worksheet.write(6, 0, "Date", bold_format)
    # worksheet.write(6, 1, "Time", bold_format)
    # worksheet.write(6, 2, "User", bold_format)
    # worksheet.write(6, 3, "Type", bold_format)
    # worksheet.write(6, 4, "Description", bold_format)
    # worksheet.write(6, 5, "Reference", bold_format)
    # worksheet.write(6, 6, "Debit", bold_format)
    # worksheet.write(6, 7, "Credit", bold_format)
    # worksheet.write(6, 8, "Balance", bold_format)

    # # Write General Ledger data (same as HTML)
    # row_idx = 7  # Start from the next row after the headers
    # for row in data:
    #     # Date formatting
    #     worksheet.write(row_idx, 0, formatdate(row.get("posting_date")) if row.get("posting_date") else "")
    #     worksheet.write(row_idx, 1, frappe.utils.format_time(frappe.db.get_value(row.voucher_type, row.voucher_no, "posting_time")))
    #     worksheet.write(row_idx, 2, frappe.db.get_value("User", frappe.db.get_value(row.voucher_type, row.voucher_no, "owner"), "full_name"))
        
    #     # Write voucher type logic (Sales, Receipt, Transfer, etc.)
    #     if frappe.db.get_value("Customer", customer, "customer_group") != "Insurance":
    #         if row.voucher_type == "Sales Invoice":
    #             if frappe.db.get_value("Sales Invoice", row.voucher_no, "is_return") == 1:
    #                 worksheet.write(row_idx, 3, "Return")    
    #             else:
    #                 worksheet.write(row_idx, 3, "Sales")
    #         elif row.voucher_type == "Payment Entry":
    #             worksheet.write(row_idx, 3, "Receipt")
    #         elif row.voucher_type == "Journal Entry":
    #             worksheet.write(row_idx, 3, "Transfer")

    #     # Write Description - Dynamic for Sales Invoice
    #     description = ""
    #     if row.voucher_type == "Sales Invoice":
    #         sales_doc = frappe.get_doc("Sales Invoice", row.voucher_no)
    #         item_group = set()
    #         for item in sales_doc.items:
    #             if item.item_group:
    #                 item_group.add(item.item_group)
            
    #         description = " | ".join(list(item_group))  # Item Groups
    #         total_invoice_amount = frappe.db.get_value("Sales Invoice", row.voucher_no, "total")
    #         discount = frappe.db.get_value("Sales Invoice", row.voucher_no, "discount_amount")
    #         # description += f" | Total: {frappe.utils.fmt_money(total_invoice_amount, currency='USD')} | Discount: {frappe.utils.fmt_money(discount, currency='USD')}"
    #         worksheet.write(row_idx, 4, description)
        
    #     elif row.voucher_type == "Payment Entry":
    #         p_d = frappe.get_doc("Payment Entry", row.voucher_no)
    #         worksheet.write(row_idx, 4, f"Paid Amount: {frappe.utils.fmt_money(p_d.paid_amount, currency='USD')} | Discount: {frappe.utils.fmt_money(row.credit - p_d.paid_amount, currency='USD')}")

    #     elif row.voucher_type == "Journal Entry":
    #         if frappe.db.get_value("Customer", customer, "customer_group") == "Insurance":
    #             worksheet.write(row_idx, 4, f"Patient: {frappe.db.get_value('Journal Entry', row.voucher_no, 'patient')} | Name: {frappe.db.get_value('Journal Entry', row.voucher_no, 'patient_name')}")
    #         else:
    #             worksheet.write(row_idx, 4, frappe.db.get_value("Journal Entry", row.voucher_no, "remark"))

    #     # Write Reference, Debit, Credit, and Balance
    #     worksheet.write(row_idx, 5, row.get("voucher_no"))
    #     worksheet.write(row_idx, 6, row.get("debit"))
    #     worksheet.write(row_idx, 7, row.get("credit"))
    #     worksheet.write(row_idx, 8, row.get("balance"))
        
    #     # Update totals dynamically
    #     total_debit += row.get("debit", 0)
    #     total_credit += row.get("credit", 0)

    #     row_idx += 1  # Move to the next row for the next data entry

    # # Update total debit and credit values after the loop
    # # worksheet.write(4, 3, total_debit)
    # # worksheet.write(4, 5, total_credit)

    # workbook.close()
    # output.seek(0)

    # # Save file to File DocType
    # filename = f"Customer-Statement-{cust_doc.customer_name}-{frappe.utils.nowdate()}.xlsx"
    # file_doc = save_file(filename, output.getvalue(), "Customer", customer, is_private=0)

    # return {"file_url": file_doc.file_url}

@frappe.whitelist()
def customer_statement_details( company, customer_name,cost_center = None, account = None, from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Customer Statements Sender")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   
    
    report_gl_filters = {
        
        "company": company,
        "party_type": "Customer",
        "party": [customer_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    if cost_center:
       frappe.errprint(cost_center)
       report_gl_filters['cost_center'] = [cost_center]
    frappe.errprint(report_gl_filters)
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    frappe.errprint(customer_name)
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": customer_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Customer Statements Sender", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/customer_statement.html",
        {
            "title": "Customer Statement for {0}".format(customer_name),
            "description": "Customer Statement for {0}".format(customer_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(customer_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": [],
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data


@frappe.whitelist()
def get_report_content( company, customer_name,cost_center = None, account = None, from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Customer Statements Sender")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   
    
    report_gl_filters = {
        
        "company": company,
        "party_type": "Customer",
        "party": [customer_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    if cost_center:
       frappe.errprint(cost_center)
       report_gl_filters['cost_center'] = [cost_center]
    frappe.errprint(report_gl_filters)
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": customer_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Customer Statements Sender", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/customer_statement_jinja.html",
        {
            "title": "Customer Statement for {0}".format(customer_name),
            "description": "Customer Statement for {0}".format(customer_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(customer_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": [],
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data

@frappe.whitelist()
def get_report_content_2( company, supplier_name, account  = None,from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Supplier Statements")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   

    report_gl_filters = {
        
        "company": company,
        "party_type": "Supplier",
        "party": [supplier_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": supplier_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Supplier Statements", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/supplier_statements.html",
        {
            "title": "Customer Statement for {0}".format(supplier_name),
            "description": "Customer Statement for {0}".format(supplier_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(supplier_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": [],
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data

@frappe.whitelist()
def get_report_content_3(company, employee_name,account  = None, from_date=None, to_date=None):
    frappe.errprint(account)
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Employee Statements")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   

    report_gl_filters = {
        
        "company": company,
        "party_type": "Employee",
        "party": [employee_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": employee_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Employee Statements", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/employee_statements.html",
        {
            "title": "Customer Statement for {0}".format(employee_name),
            "description": "Customer Statement for {0}".format(employee_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(employee_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": [],
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data


def get_file_name():
    return "{0}.{1}".format(
        "Customer Statement".replace(" ", "-").replace("/", "-"), "pdf"
    )


def get_billing_address(customer):
    pass
	

@frappe.whitelist()
def frappe_format_value(value, df=None, doc=None, currency=None, translated=False):
    from frappe.utils.formatters import format_value

    return format_value(value, df, doc, currency, translated)


@frappe.whitelist()
def send_individual_statement(customer, email_id, company, from_date, to_date):
    data = get_report_content(
        company,
        customer,
        from_date=from_date,
        to_date=to_date,
    )
    # Get PDF Data
    pdf_data = get_pdf(data)
    if not pdf_data:
        return

    attachments = [{"fname": get_file_name(), "fcontent": pdf_data}]

    if email_id == "to_find":
        email_id = frappe.get_value("Customer", customer, "email_id")
    make(
        recipients=email_id,
        send_email=True,
        subject="Customer Statement from {0}".format(company),
        content="Good day. <br> Please find attached your latest statement from {0}".format(
            company
        ),
        attachments=attachments,
        doctype="Report",
        name="General Ledger",
    )



@frappe.whitelist()
# def patient_clearance(patient):
#     cost_centers = frappe.get_all("Cost Center", filters={"is_group": 0}, pluck="name")
#     receivables = []

#     for center in cost_centers:
#         report_gl_filters = {
#             "company": frappe.defaults.get_user_default("Company"),
#             "posting_date": "Today",
#             "cost_center": [center],
#             "party_type": "Customer",
#             "party": [frappe.db.get_value('Patient', patient, 'customer')],
#             "from_date"  : frappe.utils.getdate("2000-01-01"),
#             "to_date" : frappe.utils.getdate()
#         }

#         report_gl = frappe.get_doc("Report", "General Ledger")
#         # report_gl_filters = report_gl.get_filter_values(filters)

#         columns_gl, data_gl = report_gl.get_data(
#             limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
#         )

#         if data_gl:
#             balance = data_gl[0].balance
#             receivables.append({"cost_center": center, "amount": balance})

#     return receivables


@frappe.whitelist()
def patient_clearance(**args):
    cost_center=frappe.db.sql(""" select name from `tabCost Center` where is_group not in (1)""",as_dict=True)
    bl=[]
    for center in cost_center:

        report_re = frappe.get_doc("Report", "Accounts Receivable Summary")
        customer= frappe.db.get_value('Patient', args.get("patient"),'customer')
        
        report_re_filters = {
            
            "company": frappe.defaults.get_user_default("company"),
            # "party_type": "Customer",
            "cost_center": center.name,
            "customer": customer,
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,

        }

        columns_re, data_re = report_re.get_data(
            limit=500, user="Administrator", filters=report_re_filters, as_dict=True
        )
        if data_re:
            bl.append({
            "cost_center": center.name,
            "amount": data_re[0].outstanding
            })
    return bl


# ---------------------------------print consents-------------------------
@frappe.whitelist()
def get_print_html(patient,clinical_procedure):

    report_html_data = frappe.render_template(
        "his/templates/report/consent.html",
        {
            "patient": patient,
            "clinical_procedure": clinical_procedure,
   
        },
    )

    return report_html_data



@frappe.whitelist()
def item_wise(customer , from_date ,to_date ,customer_name , detail = 1):
    # customer_name = frappe.db.get_value("Customer",customer,"customer_name")
    frappe.errprint(customer_name)

     # Get Letter Head
   
    # no_letterhead = bool(
    #     frappe.db.get_single_value("Customer Statements", "no_letter_head")
    # )
    # letter_head = frappe._dict(
    #     printview.get_letter_head(settings_doc, no_letterhead) or {}
    # )
    # if letter_head.content:
    #     letter_head.content = frappe.utils.jinja.render_template(
    #         letter_head.content, {"doc": settings_doc.as_dict()}
    #     )
    report_gl = frappe.get_doc("Report", "Item-wise Sales Register")

    report_item_wise = {
             "company": frappe.db.get_single_value("Customer Statements Sender", "company"),
             "customer" : customer,
            "from_date": from_date,
             "to_date": to_date,
            "group_by":"Item Group"  }
    col ,data_gl = report_gl.get_data(
           limit=500, user="Administrator", filters=report_item_wise, as_dict=True
         )
    l = []
    payment= []
    l_in = 0
    for index , i in enumerate(data_gl):
         if i == {}:
             frappe.errprint(index)
             if len(l) == 0:
                 l.append(data_gl[:index])
                 l_in = index
             else:
                 l.append(data_gl[l_in:index])
                 l_in = index
            #  print("\n\n\n" , l ,"\n\n\n")
    total_invoice= 0
    for t in l:
        total_invoice = total_invoice + t[-1].amount
        # frappe.errprint(t[-1].amount )
        
        # frappe.errprint(t)
    pay= frappe.db.get_list("Payment Entry", filters={'docstatus': ['=', 1] ,"posting_date": ["between", [from_date, to_date]], "party": customer}, fields=["name", "unallocated_amount","posting_date", "party", "paid_amount" ,"unallocated_amount"])
    total_receipt = 0
    for row in pay:
        # frappe.errprint()
        # payment_doc = 
        total_receipt = total_receipt+ row.unallocated_amount

    # frappe.errprint(total_receipt)
    # print("\n\n" , l ,"\n\n\n")
    net_total = get_balance_on(company = frappe.defaults.get_user_default("Company"),
						party_type ="Customer",
						party = customer,
						date = getdate())
    # for paid_sales in l:        
    paid_list = frappe.get_list("Sales Invoice", filters={'docstatus': ['=', 1] ,"customer": customer , 'paid_amount': ['>', 0] , "posting_date": ["between", [from_date, to_date]] }, fields=["docstatus","name", "customer", "posting_date", "paid_amount"])
    # frappe.errprint(paid_list)
    for inv in paid_list:
        total_receipt = total_receipt+ inv.paid_amount
    group_runign= 0
    for  group in l:
        running = 0
        group_runign = group_runign + group[-1].amount
        group[-1]['grunning'] = group_runign
        for i in group:
            if i.amount:
                running = running + i.amount or running
            i['running'] = running

    # frappe.msgprint(detail)
    report_html_data = frappe.render_template(
        "his/templates/report/customer_statement.html",
        {
            "data" : l ,
            "customer": customer,
            "customer_name": customer_name,
            "from" : from_date,
            "to" : to_date,
            "payments" : pay,
            "paid_invoices" : paid_list,
            "total_invoice" : total_invoice, 
            "total_recipt" : total_receipt,
            "net_total" : net_total,
            "detail" : int(detail)
            # "letter_head" :letter_head.content,

        }
     )
    return report_html_data



@frappe.whitelist()
def account_statement( company, account ,cost_center = None, from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   
    
    report_gl_filters = {
        
        "company": company,
        "account": [account],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
 
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )



    # Render Template

    report_html_data = frappe.render_template(
        "his/templates/report/accounts_statement.html",
        {
            "title": "ACcount Statement for {0}".format(account),
            "description": "Account Statement for {0}".format(account),
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(account),
            "filters": report_gl_filters,
        
        },
    )

    return report_html_data
