# Copyright (c) 2026
# For license information, please see license.txt

import frappe
import re
from frappe import _
from frappe.utils import getdate, today, add_days, flt, cint


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_filters(filters)

    settings = get_his_settings()
    period_days = get_period_days(filters.period)

    filters.as_on_date = getdate(filters.as_on_date or today())
    filters.from_date = add_days(filters.as_on_date, -(period_days - 1))

    columns = get_columns()
    data = get_data(filters, settings)

    chart = get_chart_data(data)
    report_summary = get_report_summary(data)

    return columns, data, None, chart, report_summary


def validate_filters(filters):
    if not filters.get("period"):
        filters.period = "Weekly"

    if filters.get("period") not in ("Weekly", "Monthly", "Quarterly"):
        frappe.throw(_("Period must be Weekly, Monthly, or Quarterly"))

    if not filters.get("as_on_date"):
        filters.as_on_date = today()


def get_his_settings():
    settings = frappe.db.get_singles_dict("HIS Settings") or {}

    return frappe._dict({
        "safety_stock_percent": flt(settings.get("pharmacy_safety_stock_percent") or 15),
        "reorder_level_percent": flt(settings.get("pharmacy_reorder_level_percent") or 20),
        "min_stock_percent": flt(settings.get("pharmacy_min_stock_percent") or 30),
        "max_stock_percent": flt(settings.get("pharmacy_max_stock_percent") or 100),
    })


def get_period_days(period):
    return {
        "Weekly": 7,
        "Monthly": 30,
        "Quarterly": 90,
    }.get(period, 7)

def normalize_status(status):
    status = status or ""
    status = re.sub(r"<[^>]*>", "", str(status)).strip()
    return status

def format_status_html(status):
    color_map = {
        "Out of Stock": "red",
        "Below Minimum": "red",
        "Below Reorder": "orange",
        "Normal": "green",
        "Overstock": "purple",
    }
    color = color_map.get(status, "black")
    return f'<span style="color:{color};font-weight:bold;">{status}</span>'

def get_columns():
    return [
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 140
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 220
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 160
        },
        {
            "label": _("Stock UOM"),
            "fieldname": "stock_uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 100
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        },
        {
            "label": _("Consumption From"),
            "fieldname": "from_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Consumption To"),
            "fieldname": "to_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Consumption Qty"),
            "fieldname": "consumption_qty",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": _("Safety Stock"),
            "fieldname": "safety_stock",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Reorder Level"),
            "fieldname": "reorder_level",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Minimum Level"),
            "fieldname": "minimum_level",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Maximum Level"),
            "fieldname": "maximum_level",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Current Stock"),
            "fieldname": "current_stock",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": _("Reorder Quantity"),
            "fieldname": "reorder_qty",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": _("Stock Status"),
            "fieldname": "status_html",
            "fieldtype": "HTML",
            "width": 130
        },
        {
            "label": _("Fast Moving Rank"),
            "fieldname": "fast_moving_rank",
            "fieldtype": "Int",
            "width": 120
        }
    ]


def get_data(filters, settings):
    consumption_map = get_consumption_map(filters)
    current_stock_map = get_current_stock_map(filters)
    item_meta_map = get_item_meta(filters, consumption_map, current_stock_map)

    rows = []

    # Rank by consumption descending
    ranked_items = sorted(
        item_meta_map.keys(),
        key=lambda x: flt(consumption_map.get(x, {}).get("consumption_qty")),
        reverse=True
    )

    rank_map = {}
    rank = 1
    for item_key in ranked_items:
        if flt(consumption_map.get(item_key, {}).get("consumption_qty")) > 0:
            rank_map[item_key] = rank
            rank += 1

    for item_key, meta in item_meta_map.items():
        item_code, warehouse = item_key

        consumption_qty = flt(consumption_map.get(item_key, {}).get("consumption_qty"))
        current_stock = flt(current_stock_map.get(item_key, 0))

        safety_stock = consumption_qty * (settings.safety_stock_percent / 100.0)
        reorder_level = (consumption_qty * (settings.reorder_level_percent / 100.0)) + safety_stock
        minimum_level = consumption_qty * (settings.min_stock_percent / 100.0)
        maximum_level = (consumption_qty * (settings.max_stock_percent / 100.0)) + safety_stock

        reorder_qty = (maximum_level - current_stock) if current_stock < reorder_level else 0
        reorder_qty = max(flt(reorder_qty), 0)

        status = get_stock_status(
            current_stock=current_stock,
            minimum_level=minimum_level,
            reorder_level=reorder_level,
            maximum_level=maximum_level
        )

        row = {
            "item_code": item_code,
            "item_name": meta.get("item_name"),
            "item_group": meta.get("item_group"),
            "stock_uom": meta.get("stock_uom"),
            "warehouse": warehouse,
            "from_date": filters.from_date,
            "to_date": filters.as_on_date,
            "consumption_qty": round(consumption_qty, 2),
            "safety_stock": round(safety_stock, 2),
            "reorder_level": round(reorder_level, 2),
            "minimum_level": round(minimum_level, 2),
            "maximum_level": round(maximum_level, 2),
            "current_stock": round(current_stock, 2),
            "reorder_qty": round(reorder_qty, 2),
            "status": status,                 # raw value for chart/summary/filter
            "status_html": format_status_html(status),
            "fast_moving_rank": rank_map.get(item_key)
        }

        if filters.get("only_reorder_items") and not (current_stock < reorder_level):
            continue

        if filters.get("status") and row["status"] != filters.get("status"):
            continue

        rows.append(row)

    # sort: highest consumption first, then reorder urgency
    rows = sorted(
        rows,
        key=lambda d: (
            status_sort_key(d.get("status")),
            -flt(d.get("consumption_qty")),
            d.get("item_code") or ""
        )
    )

    if cint(filters.get("top_fast_moving")):
        top_n = cint(filters.get("top_n") or 20)
        rows = sorted(rows, key=lambda d: -flt(d.get("consumption_qty")))[:top_n]

    return rows


def get_stock_status(current_stock, minimum_level, reorder_level, maximum_level):
    if current_stock <= 0:
        return "Out of Stock"
    elif current_stock <= minimum_level:
        return "Below Minimum"
    elif current_stock < reorder_level:
        return "Below Reorder"
    elif current_stock > maximum_level:
        return "Overstock"
    else:
        return "Normal"


def status_sort_key(status):
    order = {
        "Out of Stock": 1,
        "Below Minimum": 2,
        "Below Reorder": 3,
        "Normal": 4,
        "Overstock": 5
    }
    return order.get(status, 99)


def get_consumption_map(filters):
    """
    Consumption based on stock-out movements from Stock Ledger Entry.
    We sum absolute value of negative actual_qty.
    """
    conditions = []
    values = {
        "from_date": filters.from_date,
        "to_date": filters.as_on_date,
    }

    conditions.append("sle.is_cancelled = 0")
    conditions.append("sle.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    conditions.append("sle.actual_qty < 0")

    if filters.get("company"):
        conditions.append("sle.company = %(company)s")
        values["company"] = filters.company

    if filters.get("warehouse"):
        conditions.append("sle.warehouse = %(warehouse)s")
        values["warehouse"] = filters.warehouse

    if filters.get("item_code"):
        conditions.append("sle.item_code = %(item_code)s")
        values["item_code"] = filters.item_code

    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        values["item_group"] = filters.item_group

    # Keep stock items only
    conditions.append("IFNULL(item.disabled, 0) = 0")
    conditions.append("IFNULL(item.is_stock_item, 0) = 1")

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            sle.item_code,
            sle.warehouse,
            SUM(ABS(sle.actual_qty)) AS consumption_qty
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` item
            ON item.name = sle.item_code
        WHERE {where_clause}
        GROUP BY sle.item_code, sle.warehouse
        """,
        values=values,
        as_dict=True
    )

    out = {}
    for d in rows:
        out[(d.item_code, d.warehouse)] = {
            "consumption_qty": flt(d.consumption_qty)
        }

    return out


# def get_current_stock_map(filters):
#     conditions = []
#     values = {}

#     conditions.append("IFNULL(item.disabled, 0) = 0")
#     conditions.append("IFNULL(item.is_stock_item, 0) = 1")

#     if filters.get("company"):
#         conditions.append("bin.company = %(company)s")
#         values["company"] = filters.company

#     if filters.get("warehouse"):
#         conditions.append("bin.warehouse = %(warehouse)s")
#         values["warehouse"] = filters.warehouse

#     if filters.get("item_code"):
#         conditions.append("bin.item_code = %(item_code)s")
#         values["item_code"] = filters.item_code

#     if filters.get("item_group"):
#         conditions.append("item.item_group = %(item_group)s")
#         values["item_group"] = filters.item_group

#     where_clause = " AND ".join(conditions)

#     rows = frappe.db.sql(
#         f"""
#         SELECT
#             bin.item_code,
#             bin.warehouse,
#             SUM(IFNULL(bin.actual_qty, 0)) AS current_stock
#         FROM `tabBin` bin
#         INNER JOIN `tabItem` item
#             ON item.name = bin.item_code
#         WHERE {where_clause}
#         GROUP BY bin.item_code, bin.warehouse
#         """,
#         values=values,
#         as_dict=True
#     )

#     out = {}
#     for d in rows:
#         out[(d.item_code, d.warehouse)] = flt(d.current_stock)

#     return out

def get_current_stock_map(filters):
    conditions = []
    values = {}

    conditions.append("IFNULL(item.disabled, 0) = 0")
    conditions.append("IFNULL(item.is_stock_item, 0) = 1")

    if filters.get("warehouse"):
        conditions.append("bin.warehouse = %(warehouse)s")
        values["warehouse"] = filters.warehouse

    if filters.get("item_code"):
        conditions.append("bin.item_code = %(item_code)s")
        values["item_code"] = filters.item_code

    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        values["item_group"] = filters.item_group

    if filters.get("company"):
        conditions.append("wh.company = %(company)s")
        values["company"] = filters.company

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            bin.item_code,
            bin.warehouse,
            SUM(IFNULL(bin.actual_qty, 0)) AS current_stock
        FROM `tabBin` bin
        INNER JOIN `tabItem` item
            ON item.name = bin.item_code
        INNER JOIN `tabWarehouse` wh
            ON wh.name = bin.warehouse
        WHERE {where_clause}
        GROUP BY bin.item_code, bin.warehouse
        """,
        values=values,
        as_dict=True
    )

    out = {}
    for d in rows:
        out[(d.item_code, d.warehouse)] = flt(d.current_stock)

    return out

def get_item_meta(filters, consumption_map, current_stock_map):
    """
    Build combined item+warehouse set from:
    - items with consumption
    - items with current stock
    """
    keys = set()
    keys.update(consumption_map.keys())
    keys.update(current_stock_map.keys())

    if not keys:
        return {}

    item_codes = list({k[0] for k in keys})

    meta_rows = frappe.get_all(
        "Item",
        filters={
            "name": ["in", item_codes],
            "disabled": 0,
            "is_stock_item": 1
        },
        fields=["name", "item_name", "item_group", "stock_uom"]
    )

    item_meta = {d.name: d for d in meta_rows}

    out = {}
    for item_code, warehouse in keys:
        meta = item_meta.get(item_code)
        if not meta:
            continue

        out[(item_code, warehouse)] = {
            "item_name": meta.item_name,
            "item_group": meta.item_group,
            "stock_uom": meta.stock_uom,
        }

    return out


def get_chart_data(data):
    if not data:
        return None

    status_count = {
        "Out of Stock": 0,
        "Below Minimum": 0,
        "Below Reorder": 0,
        "Normal": 0,
        "Overstock": 0
    }

    for d in data:
        status = normalize_status(d.get("status"))
        if status in status_count:
            status_count[status] += 1

    return {
        "data": {
            "labels": list(status_count.keys()),
            "datasets": [
                {
                    "name": "Items",
                    "values": list(status_count.values())
                }
            ]
        },
        "type": "bar",
        "height": 280
    }

def get_report_summary(data):
    total_items = len(data)
    total_reorder_items = len([d for d in data if flt(d.get("reorder_qty")) > 0])
    total_out_of_stock = len([d for d in data if normalize_status(d.get("status")) == "Out of Stock"])
    total_below_minimum = len([d for d in data if normalize_status(d.get("status")) == "Below Minimum"])
    total_overstock = len([d for d in data if normalize_status(d.get("status")) == "Overstock"])

    total_reorder_qty = sum(flt(d.get("reorder_qty")) for d in data)

    return [
        {
            "label": _("Total Items"),
            "value": total_items,
            "indicator": "Blue"
        },
        {
            "label": _("Needs Reorder"),
            "value": total_reorder_items,
            "indicator": "Orange"
        },
        {
            "label": _("Out of Stock"),
            "value": total_out_of_stock,
            "indicator": "Red"
        },
        {
            "label": _("Below Minimum"),
            "value": total_below_minimum,
            "indicator": "Red"
        },
        {
            "label": _("Overstock"),
            "value": total_overstock,
            "indicator": "Purple"
        },
        {
            "label": _("Total Reorder Qty"),
            "value": round(total_reorder_qty, 2),
            "indicator": "Green"
        },
    ]

