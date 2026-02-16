import frappe
from frappe import _

def get_columns(filters):
    """
    Function to define the columns for the report dynamically.
    """
    # Determine if the report is in detailed or summary view
    detailed_view = filters.get("detailed_view")

    if detailed_view:
        # Detailed view: Show all columns except for total grand total
        columns = [
            {
                "label": _("Employee"),
                "fieldname": "employee",
                "fieldtype": "Link",
                "options": "Employee",  # This makes the employee column a link
                "width": 150
            },
            {
                "label": _("Employee Name"),
                "fieldname": "employee_name",
                "fieldtype": "Data",
                "width": 200
            },
            {
                "label": _("Posting Date"),
                "fieldname": "posting_date",
                "fieldtype": "Date",
                "width": 150
            },
            {
                "label": _("Grand Total"),
                "fieldname": "grand_total",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "label": _("Net Total"),
                "fieldname": "net_total",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "label": _("Discount Amount"),
                "fieldname": "discount_amount",
                "fieldtype": "Currency",
                "width": 150
            }
        ]
    else:
        # Summary view: Only show employee, employee name, and total grand total
        columns = [
            {
                "label": _("Employee"),
                "fieldname": "employee",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150
            },
            {
                "label": _("Employee Name"),
                "fieldname": "employee_name",
                "fieldtype": "Data",
                "width": 200
            },
            {
                "label": _("Total Grand Total"),
                "fieldname": "total_grand_total",
                "fieldtype": "Currency",
                "width": 150
            }
        ]
    
    return columns

def execute(filters=None):
    # Default filters (if none are passed)
    from_date = filters.get("from_date") if filters.get("from_date") else "2025-01-01"
    to_date = filters.get("to_date") if filters.get("to_date") else "2025-12-31"
    employee = filters.get("employee") if filters.get("employee") else None
    detailed_view = filters.get("detailed_view")  # Checkbox filter to toggle between detailed and summary view
    
    # If detailed_view is checked, we'll show detailed transactions, else summary by employee
    if detailed_view:
        # Detailed view: Show each individual transaction for each employee
        query = """
            SELECT
                employee,
                employee_name,
                posting_date,
                grand_total,
                net_total,
                discount_amount
            FROM
                `tabCanteen`
            WHERE
                docstatus = 1 AND posting_date BETWEEN %(from_date)s AND %(to_date)s
        """
        if employee:
            query += " AND employee = %(employee)s"
        query += " ORDER BY posting_date"
        
    else:
        # Summary view: Sum the grand totals by employee
        query = """
            SELECT
                employee,
                employee_name,
                SUM(grand_total) as total_grand_total
            FROM
                `tabCanteen`
            WHERE
                posting_date BETWEEN %(from_date)s AND %(to_date)s
        """
        if employee:
            query += " AND employee = %(employee)s"
        query += " GROUP BY employee"
    
    # Execute the query
    results = frappe.db.sql(query, {
        'from_date': from_date,
        'to_date': to_date,
        'employee': employee
    }, as_dict=True)

    columns = get_columns(filters)
    
    return columns, results
