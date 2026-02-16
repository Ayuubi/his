from __future__ import annotations
import frappe

PRIV_ROLES = {"System Manager", "Accounts Manager"}

def user_has_any_role(roles, user=None) -> bool:
    user = user or frappe.session.user
    user_roles = set(frappe.get_roles(user) or [])
    return any(r in user_roles for r in roles)

def _get_practitioner_for_user(user=None):
    user = user or frappe.session.user
    pr = frappe.db.get_value("Healthcare Practitioner", {"user_id": user}, "name")
    if pr:
        return pr
    return frappe.db.get_value("Healthcare Practitioner", {"user": user}, "name")

def _restrict_to_doctor(filters):
    if user_has_any_role(PRIV_ROLES):
        return
    pr = filters.get("practitioner") or _get_practitioner_for_user()
    filters["practitioner"] = pr or "__no_such_practitioner__"

def execute(filters=None):
    filters = frappe._dict(filters or {})
    _restrict_to_doctor(filters)

    _cols, rows, _, _ = frappe.get_attr(
        "his.his.report.doctor_commission_ledger.doctor_commission_ledger.execute"
    )(filters)

    # ----------------------------------------
    # Aggregation
    # ----------------------------------------
    # NOTE:
    # - item_group can be empty when sales_invoice_item is missing
    # - we treat empty group as "Unknown" but we can exclude it from main grouping
    key_fields = ["practitioner", "employee", "item_group", "source_order"]
    agg = {}

    # Keep unknown bucket separate (optional)
    unknown_key = ("__UNKNOWN__",)

    for r in rows:
        item_group = (r.get("item_group") or "").strip()
        source_order = (r.get("source_order") or "").strip()

        # Decide grouping label
        group_label = item_group if item_group else "Unknown"

        key = (
            r.get("practitioner") or "",
            r.get("employee") or "",
            group_label,
            source_order,
        )

        a = agg.setdefault(key, {
            "practitioner": r.get("practitioner"),
            "employee": r.get("employee"),
            "item_group": group_label,
            "source_order": source_order,

            "sent_count": 0,
            "not_billed_count": 0,
            "billed_count": 0,
            "paid_count": 0,
            "pending_count": 0,

            "billed_amount": 0.0,
            "commission_paid": 0.0,
        })

        a["sent_count"] += 1

        st = (r.get("status") or "").strip()

        # Use ledger status as source of truth
        if st == "Not Billed":
            a["not_billed_count"] += 1
            continue

        if st in ("Draft", "Cancelled"):
            # these are billed-related but not "submitted billed"
            # We keep them out of billed_count; still counted as sent
            continue

        if st in ("Pending", "Paid", "Reversed"):
            a["billed_count"] += 1
            a["billed_amount"] += float(r.get("net_amount") or 0)

            comm = float(r.get("commission_amount") or 0)

            if st == "Paid" and comm > 0:
                a["paid_count"] += 1
                a["commission_paid"] += comm
            elif st == "Reversed":
                # optional: treat reversal as paid_count? usually no.
                # keep it out of paid/pending counts
                pass
            else:
                # Pending (billed, but no JE/commission)
                a["pending_count"] += 1

    data = list(agg.values())

    # OPTIONAL: hide Unknown rows completely (recommended after Ledger fix)
    # If you want to show Unknown separately, keep them.
    hide_unknown = True
    if hide_unknown:
        data = [d for d in data if (d.get("item_group") or "") != "Unknown"]

    # Sort: most commission on top
    data.sort(key=lambda d: float(d.get("commission_paid") or 0), reverse=True)

    columns = [
        {"label": "Practitioner", "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 180},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": "Source Order", "fieldname": "source_order", "fieldtype": "Data", "width": 90},

        {"label": "Sent", "fieldname": "sent_count", "fieldtype": "Int", "width": 70},
        {"label": "Not Billed", "fieldname": "not_billed_count", "fieldtype": "Int", "width": 90},
        {"label": "Billed", "fieldname": "billed_count", "fieldtype": "Int", "width": 70},
        {"label": "Paid", "fieldname": "paid_count", "fieldtype": "Int", "width": 70},
        {"label": "Pending", "fieldname": "pending_count", "fieldtype": "Int", "width": 80},

        {"label": "Billed Amount", "fieldname": "billed_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Commission Paid", "fieldname": "commission_paid", "fieldtype": "Currency", "width": 130},
    ]

    # ----------------------------------------
    # Chart: Commission Paid by Item Group (Top 8)
    # Only consider rows with commission_paid > 0
    # ----------------------------------------
    by_group = {}
    for d in data:
        if float(d.get("commission_paid") or 0) <= 0:
            continue
        g = d.get("item_group") or "Unknown"
        by_group[g] = by_group.get(g, 0.0) + float(d.get("commission_paid") or 0)

    top = sorted(by_group.items(), key=lambda x: x[1], reverse=True)[:8]
    chart = {
        "data": {
            "labels": [x[0] for x in top],
            "datasets": [{"name": "Commission Paid", "values": [x[1] for x in top]}],
        },
        "type": "bar",
    }

    return columns, data, None, chart
