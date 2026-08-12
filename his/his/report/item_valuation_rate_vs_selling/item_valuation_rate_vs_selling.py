import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns()
    data = get_data(filters)
    report_summary = get_report_summary(data)

    return columns, data, None, None, report_summary


def get_columns():
    return [
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 150,
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 200,
        },
        {
            "label": _("Stock UOM"),
            "fieldname": "stock_uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 90,
        },
        {
            "label": _("Qty"),
            "fieldname": "actual_qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": _("Selling Rate"),
            "fieldname": "selling_rate",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Valuation Rate"),
            "fieldname": "valuation_rate",
            "fieldtype": "Currency",
            "width": 125,
        },
        {
            "label": _("Difference"),
            "fieldname": "difference",
            "fieldtype": "Currency",
            "width": 110,
        },
        {
            "label": _("Margin %"),
            "fieldname": "margin_percent",
            "fieldtype": "Percent",
            "width": 100,
        },
        {
            "label": _("Stock Value"),
            "fieldname": "stock_value",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 125,
        },
    ]


def get_data(filters):

    minimum_margin = flt(filters.get("minimum_margin") or 10)
    price_list = filters.get("price_list") or "Standard Selling"

    conditions = []
    values = {
        "price_list": price_list,
    }

    if filters.get("company"):
        conditions.append("w.company = %(company)s")
        values["company"] = filters.company

    if filters.get("warehouse"):
        # Include selected warehouse only
        conditions.append("b.warehouse = %(warehouse)s")
        values["warehouse"] = filters.warehouse

    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
        values["item_group"] = filters.item_group

    if filters.get("item_code"):
        conditions.append("i.name = %(item_code)s")
        values["item_code"] = filters.item_code

    condition_sql = ""

    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    rows = frappe.db.sql(
        """
        SELECT
            i.name AS item_code,
            i.item_name,
            i.item_group,
            i.stock_uom,

            b.warehouse,
            b.actual_qty,
            b.valuation_rate,
            b.stock_value,

            COALESCE(ip.price_list_rate, 0) AS selling_rate

        FROM `tabBin` b

        INNER JOIN `tabItem` i
            ON i.name = b.item_code

        INNER JOIN `tabWarehouse` w
            ON w.name = b.warehouse

        LEFT JOIN (
            SELECT
                item_code,
                MAX(price_list_rate) AS price_list_rate
            FROM `tabItem Price`
            WHERE price_list = %(price_list)s
            GROUP BY item_code
        ) ip
            ON ip.item_code = i.name

        WHERE
            i.disabled = 0
            AND i.is_stock_item = 1
            {conditions}

        ORDER BY
            i.item_group,
            i.name,
            b.warehouse

        """.format(conditions=condition_sql),
        values,
        as_dict=True,
    )

    data = []

    for row in rows:

        selling_rate = flt(row.selling_rate)
        valuation_rate = flt(row.valuation_rate)
        actual_qty = flt(row.actual_qty)

        difference = selling_rate - valuation_rate

        if selling_rate:
            margin_percent = (
                difference / selling_rate
            ) * 100
        else:
            margin_percent = 0


        # -----------------------------------------
        # STATUS
        # -----------------------------------------

        if not selling_rate:
            status = "NO SELLING PRICE"

        elif valuation_rate > selling_rate:
            status = "LOSS"

        elif valuation_rate == selling_rate:
            status = "BREAK EVEN"

        elif margin_percent < minimum_margin:
            status = "LOW MARGIN"

        else:
            status = "OK"


        row.update({
            "difference": difference,
            "margin_percent": margin_percent,
            "status": status,
        })


        # -----------------------------------------
        # FILTER: ONLY STOCK
        # -----------------------------------------

        if filters.get("only_with_stock"):
            if actual_qty <= 0:
                continue


        # -----------------------------------------
        # FILTER: VALUATION > SELLING
        # -----------------------------------------

        if filters.get("valuation_above_selling"):
            if not selling_rate:
                continue

            if valuation_rate <= selling_rate:
                continue


        # -----------------------------------------
        # STATUS FILTER
        # -----------------------------------------

        price_status = filters.get("price_status")

        if price_status and price_status != "All":

            if price_status == "Problems":

                if status not in [
                    "LOSS",
                    "BREAK EVEN",
                    "LOW MARGIN",
                    "NO SELLING PRICE",
                ]:
                    continue

            elif status != price_status:
                continue


        data.append(row)


    # Put dangerous rows first
    data.sort(
        key=lambda d: (
            get_status_priority(d.get("status")),
            flt(d.get("margin_percent")),
            d.get("item_code") or "",
            d.get("warehouse") or "",
        )
    )

    return data


def get_status_priority(status):

    priorities = {
        "LOSS": 1,
        "BREAK EVEN": 2,
        "LOW MARGIN": 3,
        "NO SELLING PRICE": 4,
        "OK": 5,
    }

    return priorities.get(status, 99)


def get_report_summary(data):

    loss_count = 0
    low_margin_count = 0
    missing_price_count = 0
    problem_stock_value = 0

    for row in data:

        status = row.get("status")

        if status == "LOSS":
            loss_count += 1

        elif status == "LOW MARGIN":
            low_margin_count += 1

        elif status == "NO SELLING PRICE":
            missing_price_count += 1

        if status in ["LOSS", "BREAK EVEN"]:
            problem_stock_value += flt(row.get("stock_value"))


    return [
        {
            "value": len(data),
            "indicator": "Blue",
            "label": _("Warehouse Item Rows"),
            "datatype": "Int",
        },
        {
            "value": loss_count,
            "indicator": "Red" if loss_count else "Green",
            "label": _("Selling Below Valuation"),
            "datatype": "Int",
        },
        {
            "value": low_margin_count,
            "indicator": "Orange" if low_margin_count else "Green",
            "label": _("Low Margin"),
            "datatype": "Int",
        },
        {
            "value": missing_price_count,
            "indicator": "Orange" if missing_price_count else "Green",
            "label": _("Missing Selling Price"),
            "datatype": "Int",
        },
        {
            "value": problem_stock_value,
            "indicator": "Red" if problem_stock_value else "Green",
            "label": _("Stock Value At Risk"),
            "datatype": "Currency",
        },
    ]