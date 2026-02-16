import frappe
from frappe import _
from frappe.utils import flt

# Who can see Income Account column
ALLOWED_ROLES_TO_SEE_INCOME_ACCOUNT = {
    "Accounts Manager",
    "System Manager",
}

# Who can run the report for ANY doctor (management)
ALLOWED_ROLES_TO_VIEW_ALL_DOCTORS = {
    "Accounts Manager",
    "System Manager",
}


# -----------------------------
# Helpers
# -----------------------------
def _has_field(doctype: str, fieldname: str) -> bool:
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _is_management_user(user=None) -> bool:
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    return bool(roles & ALLOWED_ROLES_TO_VIEW_ALL_DOCTORS)


def execute(filters=None):
    filters = filters or {}

    # Enforce: normal doctors can only see themselves (based on User Permission)
    enforce_practitioner_scope(filters)
    # commented by Hirsi to view all doctors requested by Eng Farah
    # if not filters.get("ref_practitioner"):
    #     frappe.throw(_("Please select a doctor to generate the report."))

    can_see_income = user_can_see_income_account()

    columns = get_columns(can_see_income)
    data = get_income_accounts(filters, can_see_income)

    if not data:
        return columns, []

    # Add commission columns + apply doctor visibility rule
    data = apply_commission_and_visibility(data, filters)

    if not data:
        # doctor has no commissionable item groups
        return columns, []

    # KPI cards (top summary)
    summary = get_report_summary(data)

    # Chart
    chart = get_chart(data)

    # Frappe supports: columns, data, message, chart, report_summary
    # Removed Summary by Hirsi requested by Eng Farah
    return columns, data, None, chart

# -----------------------------
# Security / Scope
# -----------------------------
def user_can_see_income_account(user=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    return bool(roles & ALLOWED_ROLES_TO_SEE_INCOME_ACCOUNT)


def enforce_practitioner_scope(filters: dict):
    """
    If user is not privileged, force ref_practitioner to user's allowed Healthcare Practitioner
    (from User Permission) and block selecting other doctors.
    """
    user = frappe.session.user
    roles = set(frappe.get_roles(user))

    # privileged users can view all
    if roles & ALLOWED_ROLES_TO_VIEW_ALL_DOCTORS:
        return

    allowed_practitioner = get_user_allowed_practitioner(user)

    if not allowed_practitioner:
        frappe.throw(
            _("You are not allowed to view other doctors. Please ask Admin to set your Practitioner User Permission.")
        )

    # If they tried to choose someone else, block
    if filters.get("ref_practitioner") and filters["ref_practitioner"] != allowed_practitioner:
        frappe.throw(_("You can only view your own sales."))

    # Force it (even if they left it empty)
    filters["ref_practitioner"] = allowed_practitioner


def get_user_allowed_practitioner(user: str):
    """
    Reads allowed Healthcare Practitioner from User Permission.
    - If default exists -> use it
    - If only one exists -> use it
    - If multiple and none default -> deny (safer)
    """
    rows = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Healthcare Practitioner"},
        fields=["for_value", "is_default", "creation"],
        order_by="is_default desc, creation asc",
        limit=10,
    )

    if not rows:
        return None

    for r in rows:
        if r.get("is_default"):
            return r.get("for_value")

    if len(rows) == 1:
        return rows[0].get("for_value")

    frappe.throw(
        _("Multiple Practitioner permissions found for your user. Please set one as Default in User Permission.")
    )


# -----------------------------
# Report Columns / Data
# -----------------------------
def get_columns(can_see_income: bool):
    cols = []
    #commented
    # if can_see_income:
    #     cols.append({
    #         "label": _("Income Account"),
    #         "fieldname": "income_account",
    #         "fieldtype": "Link",
    #         "options": "Account",
    #         "width": 250,
    #     })

    cols += [
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 250},
       {"label": _("QTY"), "fieldname": "qty", "fieldtype": "Float",  "width": 150},

        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "company_currency", "width": 150},
  
        # NEW:
        #commented
        # {"label": _("Commission %"), "fieldname": "commission_percentage", "fieldtype": "Percent", "width": 120},
        # {"label": _("Net Commission"), "fieldname": "commission_amount", "fieldtype": "Currency", "options": "company_currency", "width": 160},
    ]
    return cols


def get_income_accounts(filters, can_see_income: bool):
    conditions = ["si.docstatus = 1"]

    if filters.get("ref_practitioner"):
        conditions.append("si.ref_practitioner = %(ref_practitioner)s")

    if filters.get("company"):
        conditions.append("si.company = %(company)s")

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")

    where_clause = " where " + " and ".join(conditions)

    # Build SELECT + GROUP BY dynamically
    select_fields = ["sii.item_group", "sum(sii.base_net_amount) as total_amount" ,   "sum(sii.qty) as qty"] 
    group_by_fields = ["sii.item_group"]

    if can_see_income:
        select_fields.insert(0, "sii.income_account")
        group_by_fields.insert(0, "sii.income_account")

    rows = frappe.db.sql(
        f"""
        select
            {", ".join(select_fields)}
        from `tabSales Invoice Item` sii
        join `tabSales Invoice` si on si.name = sii.parent
        {where_clause}
        group by {", ".join(group_by_fields)}
        order by total_amount desc
        """,
        filters,
        as_dict=True
    )

    for r in rows:
        r["total_amount"] = flt(r.get("total_amount"))

    return rows


# -----------------------------
# Commission (from Practitioner child table)
# -----------------------------
def get_practitioner_commission_map(practitioner: str):
    """
    Reads commission from Healthcare Practitioner child table "commission".
    Expected child fields (based on your screenshot):
      - item_group
      - percent
      - source_order (optional, often "All")
    Returns:
      commission_map: dict[item_group] = {"percent": float, "source_order": str}
    """
    if not practitioner:
        return {}

    # safety: field existence
    if not _has_field("Healthcare Practitioner", "commission"):
        # If your fieldname is different, rename it here.
        return {}

    doc = frappe.get_doc("Healthcare Practitioner", practitioner)
    rows = doc.get("commission") or []

    out = {}
    for r in rows:
        ig = getattr(r, "item_group", None) or (r.get("item_group") if hasattr(r, "get") else None)
        pct = getattr(r, "percent", None) or (r.get("percent") if hasattr(r, "get") else None)
        so = getattr(r, "source_order", None) or (r.get("source_order") if hasattr(r, "get") else None)

        if not ig:
            continue

        out[ig] = {
            "percent": flt(pct),
            "source_order": (so or "All"),
        }

    return out


def apply_commission_and_visibility(data, filters):
    """
    - Adds commission_percentage + commission_amount
    - Doctors (non-management): only show item groups that exist in their commission table and percent > 0
    - Management: show all groups (commission 0 when missing)
    """
    practitioner = filters.get("ref_practitioner")
    is_management = _is_management_user()

    commission_map = get_practitioner_commission_map(practitioner)

    out = []
    for row in data:
        ig = row.get("item_group")

        pct = 0.0
        if ig and ig in commission_map:
            pct = flt(commission_map[ig].get("percent"))

        # Doctors: only see item groups they have commission on
        if (not is_management) and pct <= 0:
            continue

        row["commission_percentage"] = pct
        row["commission_amount"] = flt(row.get("total_amount")) * (pct / 100.0)
        out.append(row)

    return out


# -----------------------------
# Summary (Number Cards)
# -----------------------------
def get_report_summary(data):
    total = sum(flt(d.get("total_amount")) for d in data)
    total_commission = sum(flt(d.get("commission_amount")) for d in data)
    unique_groups = len({d.get("item_group") for d in data if d.get("item_group")})

    summary = [
        {
            "label": _("Total Net Sales"),
            "value": total,
            "datatype": "Currency",
            "indicator": "Green" if total > 0 else "Red",
        },
        {
            "label": _("Total Commission"),
            "value": total_commission,
            "datatype": "Currency",
            "indicator": "Blue" if total_commission > 0 else "Red",
        },
        {
            "label": _("Item Groups"),
            "value": unique_groups,
            "datatype": "Int",
            "indicator": "Purple",
        },
    ]

    # Only show Income Accounts KPI if column exists
    if data and "income_account" in data[0]:
        unique_accounts = len({d.get("income_account") for d in data if d.get("income_account")})
        summary.insert(2, {
            "label": _("Income Accounts"),
            "value": unique_accounts,
            "datatype": "Int",
            "indicator": "Orange",
        })

    # Top bucket
    top = max(data, key=lambda x: flt(x.get("total_amount") or 0), default=None)
    if top:
        bucket = []
        if top.get("item_group"):
            bucket.append(top.get("item_group"))
        if top.get("income_account"):
            bucket.append(top.get("income_account"))
        summary.append({
            "label": _("Top Bucket"),
            "value": " / ".join(bucket) if bucket else "-",
            "datatype": "Data",
            "indicator": "Green",
        })

    return summary


# -----------------------------
# Chart
# -----------------------------
def get_chart(data):
    by_group = {}
    for d in data:
        g = d.get("item_group") or _("Not Set")
        by_group[g] = by_group.get(g, 0) + flt(d.get("total_amount"))

    items = sorted(by_group.items(), key=lambda x: x[1], reverse=True)[:10]
    labels = [i[0] for i in items]
    values = [i[1] for i in items]

    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": _("Net Sales"), "values": values}],
        },
        "type": "bar",
        "height": 260,
    }


# import frappe
# from frappe import _
# from frappe.utils import flt

# # Who can see Income Account column
# ALLOWED_ROLES_TO_SEE_INCOME_ACCOUNT = {
#     "Accounts Manager",
#     "System Manager",
# }

# # Who can run the report for ANY doctor (management)
# ALLOWED_ROLES_TO_VIEW_ALL_DOCTORS = {
#     "Accounts Manager",
#     "System Manager",
# }

# def execute(filters=None):
#     filters = filters or {}

#     # Enforce: normal doctors can only see themselves (based on User Permission)
#     enforce_practitioner_scope(filters)

#     if not filters.get("ref_practitioner"):
#         frappe.throw(_("Please select a doctor to generate the report."))

#     can_see_income = user_can_see_income_account()

#     columns = get_columns(can_see_income)
#     data = get_income_accounts(filters, can_see_income)

#     if not data:
#         return columns, []

#     # KPI cards (top summary)
#     summary = get_report_summary(data)

#     # Chart
#     chart = get_chart(data)

#     # Frappe supports: columns, data, message, chart, report_summary
#     return columns, data, None, chart, summary


# # -----------------------------
# # Security / Scope
# # -----------------------------
# def user_can_see_income_account(user=None):
#     user = user or frappe.session.user
#     roles = set(frappe.get_roles(user))
#     return bool(roles & ALLOWED_ROLES_TO_SEE_INCOME_ACCOUNT)


# def enforce_practitioner_scope(filters: dict):
#     """
#     If user is not privileged, force ref_practitioner to user's allowed Healthcare Practitioner
#     (from User Permission) and block selecting other doctors.
#     """
#     user = frappe.session.user
#     roles = set(frappe.get_roles(user))

#     # privileged users can view all
#     if roles & ALLOWED_ROLES_TO_VIEW_ALL_DOCTORS:
#         return

#     allowed_practitioner = get_user_allowed_practitioner(user)

#     if not allowed_practitioner:
#         frappe.throw(
#             _("You are not allowed to view other doctors. Please ask Admin to set your Practitioner User Permission.")
#         )

#     # If they tried to choose someone else, block
#     if filters.get("ref_practitioner") and filters["ref_practitioner"] != allowed_practitioner:
#         frappe.throw(_("You can only view your own sales."))

#     # Force it (even if they left it empty)
#     filters["ref_practitioner"] = allowed_practitioner


# def get_user_allowed_practitioner(user: str):
#     """
#     Reads allowed Healthcare Practitioner from User Permission.
#     - If default exists -> use it
#     - If only one exists -> use it
#     - If multiple and none default -> deny (safer)
#     """
#     rows = frappe.get_all(
#         "User Permission",
#         filters={"user": user, "allow": "Healthcare Practitioner"},
#         fields=["for_value", "is_default", "creation"],
#         order_by="is_default desc, creation asc",
#         limit=10,
#     )

#     if not rows:
#         return None

#     for r in rows:
#         if r.get("is_default"):
#             return r.get("for_value")

#     if len(rows) == 1:
#         return rows[0].get("for_value")

#     frappe.throw(
#         _("Multiple Practitioner permissions found for your user. Please set one as Default in User Permission.")
#     )


# # -----------------------------
# # Report Columns / Data
# # -----------------------------
# def get_columns(can_see_income: bool):
#     cols = []

#     if can_see_income:
#         cols.append({
#             "label": _("Income Account"),
#             "fieldname": "income_account",
#             "fieldtype": "Link",
#             "options": "Account",
#             "width": 250,
#         })

#     cols += [
#         {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 250},
#         {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "company_currency", "width": 150},
#     ]
#     return cols


# def get_income_accounts(filters, can_see_income: bool):
#     conditions = ["si.docstatus = 1"]

#     if filters.get("ref_practitioner"):
#         conditions.append("si.ref_practitioner = %(ref_practitioner)s")

#     if filters.get("company"):
#         conditions.append("si.company = %(company)s")

#     if filters.get("from_date"):
#         conditions.append("si.posting_date >= %(from_date)s")

#     if filters.get("to_date"):
#         conditions.append("si.posting_date <= %(to_date)s")

#     where_clause = " where " + " and ".join(conditions)

#     # Build SELECT + GROUP BY dynamically
#     select_fields = ["sii.item_group", "sum(sii.base_net_amount) as total_amount"]
#     group_by_fields = ["sii.item_group"]

#     if can_see_income:
#         select_fields.insert(0, "sii.income_account")
#         group_by_fields.insert(0, "sii.income_account")

#     rows = frappe.db.sql(
#         f"""
#         select
#             {", ".join(select_fields)}
#         from `tabSales Invoice Item` sii
#         join `tabSales Invoice` si on si.name = sii.parent
#         {where_clause}
#         group by {", ".join(group_by_fields)}
#         order by total_amount desc
#         """,
#         filters,
#         as_dict=True
#     )

#     for r in rows:
#         r["total_amount"] = flt(r.get("total_amount"))

#     return rows


# # -----------------------------
# # Summary (Number Cards)
# # -----------------------------
# def get_report_summary(data):
#     total = sum(flt(d.get("total_amount")) for d in data)
#     unique_groups = len({d.get("item_group") for d in data if d.get("item_group")})

#     summary = [
#         {
#             "label": _("Total Net Sales"),
#             "value": total,
#             "datatype": "Currency",
#             "indicator": "Green" if total > 0 else "Red",
#         },
#         {
#             "label": _("Item Groups"),
#             "value": unique_groups,
#             "datatype": "Int",
#             "indicator": "Purple",
#         },
#     ]

#     # Only show Income Accounts KPI if column exists
#     if data and "income_account" in data[0]:
#         unique_accounts = len({d.get("income_account") for d in data if d.get("income_account")})
#         summary.insert(1, {
#             "label": _("Income Accounts"),
#             "value": unique_accounts,
#             "datatype": "Int",
#             "indicator": "Blue",
#         })

#     # Top bucket
#     top = max(data, key=lambda x: flt(x.get("total_amount") or 0), default=None)
#     if top:
#         bucket = []
#         if top.get("item_group"):
#             bucket.append(top.get("item_group"))
#         if top.get("income_account"):
#             bucket.append(top.get("income_account"))
#         summary.append({
#             "label": _("Top Bucket"),
#             "value": " / ".join(bucket) if bucket else "-",
#             "datatype": "Data",
#             "indicator": "Orange",
#         })

#     return summary


# # -----------------------------
# # Chart
# # -----------------------------
# def get_chart(data):
#     by_group = {}
#     for d in data:
#         g = d.get("item_group") or _("Not Set")
#         by_group[g] = by_group.get(g, 0) + flt(d.get("total_amount"))

#     items = sorted(by_group.items(), key=lambda x: x[1], reverse=True)[:10]
#     labels = [i[0] for i in items]
#     values = [i[1] for i in items]

#     return {
#         "data": {
#             "labels": labels,
#             "datasets": [{"name": _("Net Sales"), "values": values}],
#         },
#         "type": "bar",
#         "height": 260,
#     }



# import frappe
# from frappe import _
# from frappe.utils import flt

# def execute(filters=None):
#     filters = filters or {}

#     if not filters.get("ref_practitioner"):
#         frappe.throw(_("Please select a doctor to generate the report."))

#     columns = get_columns()
#     data = get_income_accounts(filters)

#     if not data:
#         return columns, []

#     # KPI cards (top summary)
#     summary = get_report_summary(data)

#     # Simple chart (dashboard feel)
#     chart = get_chart(data)

#     # Return with summary + chart
#     # Frappe supports: columns, data, message, chart, report_summary
#     return columns, data, None, chart, summary


# def get_columns():
#     return [
#         {"label": _("Income Account"), "fieldname": "income_account", "fieldtype": "Link", "options": "Account", "width": 250},
#         {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 250},
#         {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "company_currency", "width": 150},
#     ]


# def get_income_accounts(filters):
#     conditions = ["si.docstatus = 1"]

#     if filters.get("ref_practitioner"):
#         conditions.append("si.ref_practitioner = %(ref_practitioner)s")

#     if filters.get("company"):
#         conditions.append("si.company = %(company)s")

#     if filters.get("from_date"):
#         conditions.append("si.posting_date >= %(from_date)s")

#     if filters.get("to_date"):
#         conditions.append("si.posting_date <= %(to_date)s")

#     where_clause = " where " + " and ".join(conditions)

#     rows = frappe.db.sql(
#         f"""
#         select
#             sii.income_account,
#             sii.item_group,
#             sum(sii.base_net_amount) as total_amount
#         from `tabSales Invoice Item` sii
#         join `tabSales Invoice` si on si.name = sii.parent
#         {where_clause}
#         group by sii.income_account, sii.item_group
#         order by total_amount desc
#         """,
#         filters,
#         as_dict=True
#     )

#     # Ensure numeric
#     for r in rows:
#         r["total_amount"] = flt(r.get("total_amount"))

#     return rows


# def get_report_summary(data):
#     total = sum(flt(d.get("total_amount")) for d in data)
#     unique_accounts = len({d.get("income_account") for d in data if d.get("income_account")})
#     unique_groups = len({d.get("item_group") for d in data if d.get("item_group")})

#     top = max(data, key=lambda x: flt(x.get("total_amount") or 0), default=None)

#     summary = [
#         {
#             "label": _("Total Net Sales"),
#             "value": total,
#             "datatype": "Currency",
#             "indicator": "Green" if total > 0 else "Red",
#         },
#         {
#             "label": _("Income Accounts"),
#             "value": unique_accounts,
#             "datatype": "Int",
#             "indicator": "Blue",
#         },
#         {
#             "label": _("Item Groups"),
#             "value": unique_groups,
#             "datatype": "Int",
#             "indicator": "Purple",
#         },
#     ]

#     if top:
#         summary.append({
#             "label": _("Top Bucket"),
#             "value": f"{top.get('item_group') or '-'} / {top.get('income_account') or '-'}",
#             "datatype": "Data",
#             "indicator": "Orange",
#         })

#     return summary


# def get_chart(data):
#     # Top 10 item groups by amount
#     by_group = {}
#     for d in data:
#         g = d.get("item_group") or _("Not Set")
#         by_group[g] = by_group.get(g, 0) + flt(d.get("total_amount"))

#     items = sorted(by_group.items(), key=lambda x: x[1], reverse=True)[:10]
#     labels = [i[0] for i in items]
#     values = [i[1] for i in items]

#     return {
#         "data": {
#             "labels": labels,
#             "datasets": [{"name": _("Net Sales"), "values": values}],
#         },
#         "type": "bar",
#         "height": 260,
#     }


# import frappe
# from frappe import _, msgprint
# from frappe.utils import flt

# def execute(filters=None):
#     if not filters:
#         filters = {}
    
#     if not filters.get("ref_practitioner"):
#         msgprint(_("Please select a doctor to generate the report."), raise_exception=True)
    
#     income_accounts = get_income_accounts(filters)
#     columns = get_columns()
    
#     if not income_accounts:
#         msgprint(_("No income accounts found for the selected doctor."))
#         return columns, []
    
#     data = []
#     for account in income_accounts:
#         data.append({
#             "income_account": account.income_account,
#             "total_amount": account.total_amount
#         })
    
#     return columns, data

# def get_columns():
#     return [
#         {"label": _( "Income Account"), "fieldname": "income_account", "fieldtype": "Data", "width": 250},
#         {"label": _( "Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 250},
#         {"label": _( "Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "currency", "width": 150}
#     ]

# def get_income_accounts(filters):
#     conditions = "where si.docstatus = 1"
#     if filters.get("ref_practitioner"):
#         conditions += " and si.ref_practitioner = %(ref_practitioner)s"
#     if filters.get("from_date"):
#         conditions += " and si.posting_date >= %(from_date)s"
#     if filters.get("to_date"):
#         conditions += " and si.posting_date <= %(to_date)s"
    
#     return frappe.db.sql(
#         f"""
#         select sii.income_account, sii.item_group, sum(sii.base_net_amount) as total_amount
#         from `tabSales Invoice Item` sii
#         join `tabSales Invoice` si on si.name = sii.parent
#         {conditions}
#         group by sii.income_account, sii.item_group
#         """,
#         filters,
#         as_dict=True
#     )
