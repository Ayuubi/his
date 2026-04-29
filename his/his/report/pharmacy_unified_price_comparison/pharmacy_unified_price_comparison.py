# Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns()
    data = get_data(filters)
    # chart = get_chart(data)
    # summary = get_report_summary(data)

    # return columns, data, None, chart, summary
    return columns, data, None


# ---------------------------------------------------------
# Columns
# ---------------------------------------------------------

def get_columns():
    return [
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 160,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 240,
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 140,
        },
        {
            "label": _("Brand"),
            "fieldname": "brand",
            "fieldtype": "Link",
            "options": "Brand",
            "width": 120,
            "hidden": 1,
        },
        {
            "label": _("Purchase UOM"),
            "fieldname": "purchase_uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 110,
        },
        {
            "label": _("Buying Price"),
            "fieldname": "buying_price",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Buying Price List"),
            "fieldname": "buying_price_list",
            "fieldtype": "Link",
            "options": "Price List",
            "width": 150,
        },
        {
            "label": _("Buying Currency"),
            "fieldname": "buying_currency",
            "fieldtype": "Link",
            "options": "Currency",
            "width": 100,
            "hidden": 1,
        },
        {
            "label": _("Sales UOM"),
            "fieldname": "sales_uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 110,
        },
        {
            "label": _("Selling Price"),
            "fieldname": "selling_price",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Selling Price List"),
            "fieldname": "selling_price_list",
            "fieldtype": "Link",
            "options": "Price List",
            "width": 150,
        },
        {
            "label": _("Selling Currency"),
            "fieldname": "selling_currency",
            "fieldtype": "Link",
            "options": "Currency",
            "width": 100,
            "hidden": 1,
        },
        {
            "label": _("Conversion Factor"),
            "fieldname": "conversion_factor",
            "fieldtype": "Float",
            "precision": 6,
            "width": 130,
            "hidden": 1,
        },
        {
            "label": _("Selling Price in Purchase UOM"),
            "fieldname": "selling_price_in_purchase_uom",
            "fieldtype": "Currency",
            "width": 190,
            "hidden": 1,
        },
        {
            "label": _("Gross Margin"),
            "fieldname": "gross_margin",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Gross Margin %"),
            "fieldname": "gross_margin_percent",
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "label": _("Conversion Source"),
            "fieldname": "conversion_source",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


# ---------------------------------------------------------
# Main Data
# ---------------------------------------------------------

def get_data(filters):
    items = get_items(filters)
    if not items:
        return []

    item_codes = [d.item_code for d in items]

    buying_prices = get_item_prices(
        item_codes=item_codes,
        price_list=filters.get("buying_price_list"),
        price_type="buying",
    )

    selling_prices = get_item_prices(
        item_codes=item_codes,
        price_list=filters.get("selling_price_list"),
        price_type="selling",
    )

    uom_map = get_uom_conversion_map(item_codes)

    data = []

    for item in items:
        purchase_uom = item.purchase_uom or item.stock_uom
        sales_uom = item.sales_uom or item.stock_uom

        buying_price_row = pick_best_price_row(
            price_rows=buying_prices.get(item.item_code, []),
            preferred_uom=purchase_uom,
            fallback_uom=item.stock_uom,
        )

        selling_price_row = pick_best_price_row(
            price_rows=selling_prices.get(item.item_code, []),
            preferred_uom=sales_uom,
            fallback_uom=item.stock_uom,
        )

        row = frappe._dict({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "brand": item.brand,
            "purchase_uom": purchase_uom,
            "buying_price": None,
            "buying_price_list": None,
            "buying_currency": None,
            "sales_uom": sales_uom,
            "selling_price": None,
            "selling_price_list": None,
            "selling_currency": None,
            "conversion_factor": None,
            "selling_price_in_purchase_uom": None,
            "gross_margin": None,
            "gross_margin_percent": None,
            "conversion_source": None,
            "status": "No Price",
        })

        # ---------------------------------
        # Buying side
        # ---------------------------------
        if buying_price_row:
            row.buying_price = flt(buying_price_row.price_list_rate)
            row.buying_price_list = buying_price_row.price_list
            row.buying_currency = buying_price_row.currency
            row.purchase_uom = buying_price_row.uom or row.purchase_uom or item.stock_uom

        # ---------------------------------
        # Selling side
        # ---------------------------------
        if selling_price_row:
            row.selling_price = flt(selling_price_row.price_list_rate)
            row.selling_price_list = selling_price_row.price_list
            row.selling_currency = selling_price_row.currency
            row.sales_uom = selling_price_row.uom or row.sales_uom or item.stock_uom

        # ---------------------------------
        # Status determination before conversion
        # ---------------------------------
        if row.buying_price and row.selling_price:
            row.status = "Has Buy & Sell"
        elif row.buying_price and not row.selling_price:
            row.status = "Missing Selling Price"
        elif row.selling_price and not row.buying_price:
            row.status = "Missing Buying Price"
        else:
            row.status = "No Price"

        # ---------------------------------
        # Conversion and margin
        # ---------------------------------
        if row.buying_price and row.selling_price:
            if (row.purchase_uom or "") == (row.sales_uom or ""):
                row.conversion_factor = 1
                row.selling_price_in_purchase_uom = flt(row.selling_price)
                row.conversion_source = "Same UOM"
                row.status = "OK"

            else:
                factor = get_conversion_factor_between_uoms(
                    item_code=item.item_code,
                    from_uom=row.sales_uom,
                    to_uom=row.purchase_uom,
                    uom_map=uom_map,
                )

                if factor:
                    row.conversion_factor = factor
                    row.selling_price_in_purchase_uom = flt(row.selling_price) * flt(factor)
                    row.conversion_source = "Item UOM"
                    row.status = "OK"
                else:
                    row.conversion_source = "Missing"
                    row.status = "Conversion Missing"

            if row.buying_price and row.selling_price_in_purchase_uom:
                row.gross_margin = flt(row.selling_price_in_purchase_uom) - flt(row.buying_price)
                if flt(row.buying_price):
                    row.gross_margin_percent = (flt(row.gross_margin) / flt(row.buying_price)) * 100

        if filters.get("show_only_with_both_prices") and not (row.buying_price and row.selling_price):
            continue

        if filters.get("show_only_ok_rows") and row.status != "OK":
            continue

        data.append(apply_row_highlight(row))

    return data


# ---------------------------------------------------------
# Items
# ---------------------------------------------------------

def get_items(filters):
    conditions = ["item.disabled = 0", "item.is_stock_item = 1"]
    values = {}

    if filters.get("item"):
        conditions.append("item.name = %(item)s")
        values["item"] = filters.get("item")

    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        values["item_group"] = filters.get("item_group")

    if filters.get("brand"):
        conditions.append("item.brand = %(brand)s")
        values["brand"] = filters.get("brand")

    # Standard ERPNext fields usually available on Item
    purchase_uom_field = "purchase_uom" if has_field("Item", "purchase_uom") else None
    sales_uom_field = "sales_uom" if has_field("Item", "sales_uom") else None

    purchase_uom_select = f"item.{purchase_uom_field} as purchase_uom," if purchase_uom_field else "NULL as purchase_uom,"
    sales_uom_select = f"item.{sales_uom_field} as sales_uom," if sales_uom_field else "NULL as sales_uom,"

    return frappe.db.sql(
        f"""
        SELECT
            item.name as item_code,
            item.item_name,
            item.item_group,
            item.brand,
            item.stock_uom,
            {purchase_uom_select}
            {sales_uom_select}
            item.disabled
        FROM `tabItem` item
        WHERE {" AND ".join(conditions)}
        ORDER BY item.item_name ASC
        """,
        values=values,
        as_dict=True,
    )


# ---------------------------------------------------------
# Item Price
# ---------------------------------------------------------

def get_item_prices(item_codes, price_list=None, price_type=None):
    if not item_codes:
        return {}

    # conditions = ["ip.item_code IN %(item_codes)s", "IFNULL(ip.uom, '') != ''"]
    conditions = ["ip.item_code IN %(item_codes)s"]
    values = {"item_codes": tuple(item_codes)}

    if has_field("Item Price", "enabled"):
        conditions.append("IFNULL(ip.enabled, 1) = 1")

    if price_list:
        conditions.append("ip.price_list = %(price_list)s")
        values["price_list"] = price_list

    if price_type == "buying" and has_field("Item Price", "buying"):
        conditions.append("IFNULL(ip.buying, 0) = 1")

    if price_type == "selling" and has_field("Item Price", "selling"):
        conditions.append("IFNULL(ip.selling, 0) = 1")

    order_parts = []
    if has_field("Item Price", "valid_from"):
        order_parts.append("ip.valid_from DESC")
    if has_field("Item Price", "modified"):
        order_parts.append("ip.modified DESC")
    else:
        order_parts.append("ip.creation DESC")

    rows = frappe.db.sql(
        f"""
        SELECT
            ip.name,
            ip.item_code,
            ip.price_list,
            ip.uom,
            ip.currency,
            ip.price_list_rate
        FROM `tabItem Price` ip
        WHERE {" AND ".join(conditions)}
        ORDER BY ip.item_code ASC, {", ".join(order_parts)}
        """,
        values=values,
        as_dict=True,
    )

    out = {}
    for d in rows:
        out.setdefault(d.item_code, []).append(d)

    return out


def pick_best_price_row(price_rows, preferred_uom=None, fallback_uom=None):
    if not price_rows:
        return None

    # Exact preferred UOM match
    if preferred_uom:
        for row in price_rows:
            if (row.uom or "") == preferred_uom:
                return row

    # Exact fallback UOM match
    if fallback_uom:
        for row in price_rows:
            if (row.uom or "") == fallback_uom:
                return row

    # ERPNext sometimes has Item Price with blank UOM.
    # Treat blank UOM as usable fallback.
    for row in price_rows:
        if not row.uom:
            return row

    return price_rows[0]


# ---------------------------------------------------------
# UOM Conversion
# ---------------------------------------------------------

def get_uom_conversion_map(item_codes):
    """
    Returns:
    {
        "ITEM-001": {
            "Piece": 1,
            "Box": 10,
            "Strip": 2
        }
    }

    Meaning each UOM conversion factor is relative to stock uom logic
    maintained in ERPNext child table.
    """
    out = {}

    if not item_codes:
        return out

    child_table = "UOM Conversion Detail"
    if not frappe.db.table_exists(f"tab{child_table}"):
        return out

    rows = frappe.db.sql(
        """
        SELECT
            parent as item_code,
            uom,
            conversion_factor
        FROM `tabUOM Conversion Detail`
        WHERE parenttype = 'Item'
          AND parent IN %(item_codes)s
        """,
        {"item_codes": tuple(item_codes)},
        as_dict=True,
    )

    for d in rows:
        out.setdefault(d.item_code, {})
        out[d.item_code][d.uom] = flt(d.conversion_factor)

    return out


def get_conversion_factor_between_uoms(item_code, from_uom, to_uom, uom_map):
    """
    We want to convert selling price from sales_uom into purchase_uom.

    If child table says:
        Piece = 1
        Box = 10

    Then:
        1 Box = 10 Piece

    To convert price per Piece into price per Box:
        factor = to_factor / from_factor = 10 / 1 = 10
    """
    if not item_code or not from_uom or not to_uom:
        return None

    item_uoms = uom_map.get(item_code, {})

    from_factor = flt(item_uoms.get(from_uom))
    to_factor = flt(item_uoms.get(to_uom))

    if not from_factor or not to_factor:
        return None

    return flt(to_factor) / flt(from_factor)


# ---------------------------------------------------------
# UI Helpers
# ---------------------------------------------------------

def apply_row_highlight(row):
    status = row.get("status")

    if status == "OK":
        row["status"] = f"<span style='color:#0f5132;font-weight:600;'>{frappe.bold(status)}</span>"
    elif status == "Conversion Missing":
        row["status"] = f"<span style='color:#b54708;font-weight:600;'>{frappe.bold(status)}</span>"
    elif status in ("Missing Buying Price", "Missing Selling Price"):
        row["status"] = f"<span style='color:#b42318;font-weight:600;'>{frappe.bold(status)}</span>"
    else:
        row["status"] = f"<span style='color:#667085;font-weight:600;'>{frappe.bold(status)}</span>"

    return row


# ---------------------------------------------------------
# Chart / Summary
# ---------------------------------------------------------

def get_chart(data):
    if not data:
        return None

    counts = {
        "OK": 0,
        "Conversion Missing": 0,
        "Missing Buying Price": 0,
        "Missing Selling Price": 0,
        "No Price": 0,
    }

    for d in data:
        raw_status = strip_html_status(d.get("status"))
        if raw_status in counts:
            counts[raw_status] += 1

    return {
        "data": {
            "labels": list(counts.keys()),
            "datasets": [
                {
                    "name": "Items",
                    "values": list(counts.values()),
                }
            ],
        },
        "type": "bar",
        "height": 280,
    }


def get_report_summary(data):
    total = len(data)
    ok_count = 0
    conversion_missing = 0
    margin_items = 0
    total_margin = 0

    for d in data:
        raw_status = strip_html_status(d.get("status"))

        if raw_status == "OK":
            ok_count += 1

        if raw_status == "Conversion Missing":
            conversion_missing += 1

        if d.get("gross_margin") is not None:
            margin_items += 1
            total_margin += flt(d.get("gross_margin"))

    return [
        {
            "value": total,
            "label": _("Total Items"),
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": ok_count,
            "label": _("Comparable Items"),
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "value": conversion_missing,
            "label": _("Conversion Missing"),
            "datatype": "Int",
            "indicator": "Orange",
        },
        {
            "value": total_margin,
            "label": _("Total Gross Margin"),
            "datatype": "Currency",
            "indicator": "Green" if total_margin >= 0 else "Red",
        },
    ]


def strip_html_status(status):
    if not status:
        return ""
    return frappe.utils.strip_html(status).strip()


# ---------------------------------------------------------
# Misc Helpers
# ---------------------------------------------------------

def has_field(doctype, fieldname):
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False