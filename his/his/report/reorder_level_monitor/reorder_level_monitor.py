import frappe
from frappe.utils import flt

def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data)

    return columns, data, None, chart


def get_columns(filters):
    cols = [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
        {"label": "Brand", "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 120, "hidden": 1},
        {"label": "UOM", "fieldname": "stock_uom", "fieldtype": "Data", "width": 80},
    ]

    if filters.get("warehouse"):
        cols.append({"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 180})

    cols += [
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 110},
    ]

    if filters.get("warehouse") and filters.get("show_all_wh_total"):
        cols.append({"label": "All WH Total", "fieldname": "all_wh_total", "fieldtype": "Float", "width": 120})

    cols += [
        {"label": "Warning Level", "fieldname": "warning_level", "fieldtype": "Float", "width": 120},
        {"label": "Danger Level", "fieldname": "danger_level", "fieldtype": "Float", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]
    return cols


def get_data(filters):
    cond = []
    values = {}

    # Item filters
    if filters.get("item_group"):
        cond.append("i.item_group = %(item_group)s")
        values["item_group"] = filters.item_group

    if filters.get("brand"):
        cond.append("i.brand = %(brand)s")
        values["brand"] = filters.brand

    if filters.get("only_stock_items"):
        cond.append("i.is_stock_item = 1")

    # Company filter (optional; Bin doesn't have company, but Item Default can)
    # If you need strict company scoping, we can join tabItem Default (optional)
    join_item_default = False
    if filters.get("company"):
        join_item_default = True
        cond.append("id.company = %(company)s")
        values["company"] = filters.company

    where_sql = ("WHERE " + " AND ".join(cond)) if cond else ""

    warehouse = filters.get("warehouse")
    status_filter = (filters.get("status") or "").strip()

    if not warehouse:
        # Total across ALL warehouses
        sql = f"""
            SELECT
                i.name AS item_code,
                i.item_name,
                i.item_group,
                i.brand,
                i.stock_uom,
                COALESCE(i.warning_level, 0) AS warning_level,
                COALESCE(i.danger_level, 0) AS danger_level,
                COALESCE(SUM(b.actual_qty), 0) AS qty
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON b.item_code = i.name
            {"LEFT JOIN `tabItem Default` id ON id.parent = i.name" if join_item_default else ""}
            {where_sql}
            GROUP BY i.name
        """
        rows = frappe.db.sql(sql, values, as_dict=True)

        for r in rows:
            r["status"] = compute_status(r["qty"], r["warning_level"], r["danger_level"])

        if status_filter:
            rows = [r for r in rows if r["status"] == status_filter]

        # show only items that have thresholds? (optional) - uncomment if you want:
        # rows = [r for r in rows if flt(r["warning_level"]) > 0 or flt(r["danger_level"]) > 0]

        return sort_rows(rows)

    # Warehouse selected: qty is for that warehouse
    values["warehouse"] = warehouse

    if filters.get("show_all_wh_total"):
        sql = f"""
            SELECT
                i.name AS item_code,
                i.item_name,
                i.item_group,
                i.brand,
                i.stock_uom,
                %(warehouse)s AS warehouse,
                COALESCE(i.warning_level, 0) AS warning_level,
                COALESCE(i.danger_level, 0) AS danger_level,
                COALESCE(bw.actual_qty, 0) AS qty,
                COALESCE(bt.total_qty, 0) AS all_wh_total
            FROM `tabItem` i
            LEFT JOIN `tabBin` bw
                ON bw.item_code = i.name AND bw.warehouse = %(warehouse)s
            LEFT JOIN (
                SELECT item_code, SUM(actual_qty) AS total_qty
                FROM `tabBin`
                GROUP BY item_code
            ) bt ON bt.item_code = i.name
            {"LEFT JOIN `tabItem Default` id ON id.parent = i.name" if join_item_default else ""}
            {where_sql}
        """
    else:
        sql = f"""
            SELECT
                i.name AS item_code,
                i.item_name,
                i.item_group,
                i.brand,
                i.stock_uom,
                %(warehouse)s AS warehouse,
                COALESCE(i.warning_level, 0) AS warning_level,
                COALESCE(i.danger_level, 0) AS danger_level,
                COALESCE(bw.actual_qty, 0) AS qty
            FROM `tabItem` i
            LEFT JOIN `tabBin` bw
                ON bw.item_code = i.name AND bw.warehouse = %(warehouse)s
            {"LEFT JOIN `tabItem Default` id ON id.parent = i.name" if join_item_default else ""}
            {where_sql}
        """

    rows = frappe.db.sql(sql, values, as_dict=True)

    for r in rows:
        r["status"] = compute_status(r["qty"], r["warning_level"], r["danger_level"])

    if status_filter:
        rows = [r for r in rows if r["status"] == status_filter]

    return sort_rows(rows)


def compute_status(qty, warning_level, danger_level):
    qty = flt(qty)
    w = flt(warning_level)
    d = flt(danger_level)

    # If danger is set and qty <= danger -> DANGER
    if d and qty <= d:
        return "DANGER"

    # If warning is set and qty <= warning -> WARNING
    if w and qty <= w:
        return "WARNING"

    return "OK"


def sort_rows(rows):
    # DANGER first, then WARNING, then OK; within that, lowest qty first
    rank = {"DANGER": 0, "WARNING": 1, "OK": 2}
    rows.sort(key=lambda r: (rank.get(r.get("status"), 9), flt(r.get("qty"))))
    return rows


def get_chart(data):
    # Simple chart: count by status
    counts = {"DANGER": 0, "WARNING": 0, "OK": 0}
    for d in data:
        s = d.get("status")
        if s in counts:
            counts[s] += 1

    return {
        "data": {
            "labels": ["DANGER", "WARNING", "OK"],
            "datasets": [{"name": "Items", "values": [counts["DANGER"], counts["WARNING"], counts["OK"]]}],
        },
        "type": "bar",
    }