import frappe
from frappe import _
from frappe.utils import getdate


def _has_field(doctype: str, fieldname: str) -> bool:
	try:
		return bool(frappe.get_meta(doctype).get_field(fieldname))
	except Exception:
		return False


def _pick_first_existing_field(doctype: str, candidates: list[str]) -> str | None:
	for f in candidates:
		if _has_field(doctype, f):
			return f
	return None


# def execute(filters=None):
# 	filters = filters or {}
# 	return get_columns(), get_data(filters)

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)

    # ✅ server-side KPI cards
    report_summary = get_report_summary(filters)

    # return 5-tuple: columns, data, message, chart, report_summary
    return columns, data, None, None, report_summary

def get_columns():
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("Time"), "fieldname": "posting_time", "fieldtype": "Time", "width": 70},

		{"label": _("Invoice"), "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
		{"label": _("Status"), "fieldname": "inv_status", "fieldtype": "Data", "width": 95},

		{"label": _("Patient ID"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 130},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 200},

		# ✅ keep ONE doctor column only
		{"label": _("Doctor"), "fieldname": "doctor_name", "fieldtype": "Data", "width": 220},

		# ✅ rename cashier to Created By
		{"label": _("Created By"), "fieldname": "created_by", "fieldtype": "Link", "options": "User", "width": 170},
		{"label": _("Created By Name"), "fieldname": "created_by_name", "fieldtype": "Data", "width": 200},

		# ✅ cancelled by
		{"label": _("Cancelled By"), "fieldname": "cancelled_by", "fieldtype": "Link", "options": "User", "width": 170},
		{"label": _("Cancelled By Name"), "fieldname": "cancelled_by_name", "fieldtype": "Data", "width": 200},

		# ✅ Total BEFORE Discount + Grand Total AFTER Discount
		{"label": _("Total (Before Discount)"), "fieldname": "total_before_discount", "fieldtype": "Currency", "width": 160},
		{"label": _("Grand Total (After Discount)"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 170},

		{"label": _("Discount Amount"), "fieldname": "discount_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Discount %"), "fieldname": "discount_percent", "fieldtype": "Percent", "width": 110},

		{"label": _("Paid"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Outstanding"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},

		{"label": _("Return"), "fieldname": "is_return", "fieldtype": "Check", "width": 70},
		{"label": _("Remark"), "fieldname": "user_remark", "fieldtype": "Data", "width": 280},

		{"label": _("Modified"), "fieldname": "modified", "fieldtype": "Datetime", "width": 160},
	]


def get_data(filters):
	from_date = getdate(filters.get("from_date")) if filters.get("from_date") else getdate()
	to_date = getdate(filters.get("to_date")) if filters.get("to_date") else getdate()

	limit = int(filters.get("row_limit") or 1500)
	if limit <= 0:
		limit = 1500
	if limit > 10000:
		limit = 10000

	# Your env: doctor field is ref_practitioner
	doctor_field = _pick_first_existing_field("Sales Invoice", ["ref_practitioner", "practitioner", "doctor"])
	patient_field = _pick_first_existing_field("Sales Invoice", ["patient", "patient_id"])
	patient_name_field = _pick_first_existing_field("Sales Invoice", ["patient_name"])

	remark_field = _pick_first_existing_field(
		"Sales Invoice",
		["user_remark", "cashier_remark", "remarks", "customer_remarks"]
	)

	doctor_sql = f"si.`{doctor_field}`" if doctor_field else "NULL"
	patient_sql = f"si.`{patient_field}`" if patient_field else "NULL"
	patient_name_sql = f"si.`{patient_name_field}`" if patient_name_field else "NULL"
	remark_sql = f"si.`{remark_field}`" if remark_field else "NULL"

	where = [
		"si.posting_date between %(from_date)s and %(to_date)s",
		# ✅ remove drafts from report by default
		"si.docstatus in (1, 2)"
	]
	params = {"from_date": from_date, "to_date": to_date, "limit": limit}

	# Optional filters
	if filters.get("invoice"):
		where.append("si.name = %(invoice)s")
		params["invoice"] = filters["invoice"]

	if filters.get("patient") and patient_field:
		where.append(f"{patient_sql} = %(patient)s")
		params["patient"] = filters["patient"]

	if filters.get("doctor") and doctor_field:
		where.append(f"{doctor_sql} = %(doctor)s")
		params["doctor"] = filters["doctor"]

	if filters.get("created_by"):
		where.append("si.owner = %(created_by)s")
		params["created_by"] = filters["created_by"]

	if filters.get("only_discounted"):
		where.append("(IFNULL(si.discount_amount, 0) > 0 OR IFNULL(si.additional_discount_percentage, 0) > 0)")

	# Status filter (no Draft anymore)
	status_filter = (filters.get("status") or "").strip()
	if status_filter == "Cancelled":
		where.append("si.docstatus = 2")
	elif status_filter == "Return":
		where.append("IFNULL(si.is_return, 0) = 1 AND si.docstatus < 2")
	elif status_filter == "Paid":
		where.append("si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.outstanding_amount, 0) = 0")
	elif status_filter == "Credit":
		where.append("si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.outstanding_amount, 0) > 0")
	

	where_sql = " AND ".join(where)

	sql = """
		SELECT
			si.posting_date,
			si.posting_time,
			si.name AS invoice,

			CASE
				WHEN si.docstatus = 2 THEN 'Cancelled'
				WHEN IFNULL(si.is_return, 0) = 1 THEN 'Return'
				WHEN si.docstatus = 1 AND IFNULL(si.outstanding_amount, 0) = 0 THEN 'Paid'
				WHEN si.docstatus = 1 AND IFNULL(si.outstanding_amount, 0) > 0 THEN 'Credit'
				ELSE 'Submitted'
			END AS inv_status,

			{patient_sql} AS patient,
			{patient_name_sql} AS patient_name,

			hp.practitioner_name AS doctor_name,

			si.owner AS created_by,
			u_owner.full_name AS created_by_name,

			CASE WHEN si.docstatus = 2 THEN si.modified_by ELSE NULL END AS cancelled_by,
			u_cancel.full_name AS cancelled_by_name,

			-- computed discount amount
			CASE
			WHEN IFNULL(si.discount_amount, 0) > 0 THEN IFNULL(si.discount_amount, 0)
			WHEN IFNULL(si.additional_discount_percentage, 0) > 0
				AND (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)) > 0
			THEN ROUND(
					(IFNULL(si.grand_total, 0) / (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)))
					- IFNULL(si.grand_total, 0)
				, 2)
			ELSE 0
			END AS discount_amount,

			-- total before discount
			ROUND(
			IFNULL(si.grand_total, 0) +
			(
				CASE
				WHEN IFNULL(si.discount_amount, 0) > 0 THEN IFNULL(si.discount_amount, 0)
				WHEN IFNULL(si.additional_discount_percentage, 0) > 0
					AND (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)) > 0
				THEN ROUND(
						(IFNULL(si.grand_total, 0) / (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)))
						- IFNULL(si.grand_total, 0)
					, 2)
				ELSE 0
				END
			)
			, 2) AS total_before_discount,

			-- discount percent (prefer field else compute)
			CASE
			WHEN IFNULL(si.additional_discount_percentage, 0) > 0 THEN IFNULL(si.additional_discount_percentage, 0)
			ELSE
				CASE
				WHEN (
					IFNULL(si.grand_total, 0) +
					(
					CASE
						WHEN IFNULL(si.discount_amount, 0) > 0 THEN IFNULL(si.discount_amount, 0)
						WHEN IFNULL(si.additional_discount_percentage, 0) > 0
							AND (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)) > 0
						THEN ROUND(
							(IFNULL(si.grand_total, 0) / (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)))
							- IFNULL(si.grand_total, 0)
							, 2)
						ELSE 0
					END
					)
				) > 0
				THEN ROUND(
					(
					(CASE
						WHEN IFNULL(si.discount_amount, 0) > 0 THEN IFNULL(si.discount_amount, 0)
						WHEN IFNULL(si.additional_discount_percentage, 0) > 0
							AND (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)) > 0
						THEN ROUND(
							(IFNULL(si.grand_total, 0) / (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)))
							- IFNULL(si.grand_total, 0)
							, 2)
						ELSE 0
					END)
					/
					(IFNULL(si.grand_total, 0) +
					(CASE
						WHEN IFNULL(si.discount_amount, 0) > 0 THEN IFNULL(si.discount_amount, 0)
						WHEN IFNULL(si.additional_discount_percentage, 0) > 0
							AND (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)) > 0
						THEN ROUND(
								(IFNULL(si.grand_total, 0) / (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)))
								- IFNULL(si.grand_total, 0)
							, 2)
						ELSE 0
						END))
					) * 100
				, 2)
				ELSE 0
				END
			END AS discount_percent,

			si.grand_total,
			(IFNULL(si.grand_total, 0) - IFNULL(si.outstanding_amount, 0)) AS paid_amount,
			si.outstanding_amount,

			IFNULL(si.is_return, 0) AS is_return,

			{remark_sql} AS user_remark,
			si.modified

		FROM `tabSales Invoice` si
		LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = {doctor_sql}
		LEFT JOIN `tabUser` u_owner ON u_owner.name = si.owner
		LEFT JOIN `tabUser` u_cancel ON u_cancel.name = (CASE WHEN si.docstatus = 2 THEN si.modified_by ELSE NULL END)

		WHERE {where_sql}
		ORDER BY si.posting_date DESC, si.posting_time DESC, si.modified DESC
		LIMIT %(limit)s
	""".format(
		patient_sql=patient_sql,
		patient_name_sql=patient_name_sql,
		doctor_sql=doctor_sql,
		remark_sql=remark_sql,
		where_sql=where_sql,
	)

	return frappe.db.sql(sql, params, as_dict=True)


def get_report_summary(filters):
    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else getdate()
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else getdate()

    # fields same as detail query
    remark_field = _pick_first_existing_field(
        "Sales Invoice",
        ["user_remark", "cashier_remark", "remarks", "customer_remarks"]
    )
    remark_sql = f"si.`{remark_field}`" if remark_field else "NULL"

    # Base conditions (same as your report: only submitted/cancelled)
    where = [
        "si.posting_date between %(from_date)s and %(to_date)s",
        "si.docstatus in (1, 2)"
    ]
    params = {"from_date": from_date, "to_date": to_date}

    # Optional filters (match your JS filters)
    if filters.get("invoice"):
        where.append("si.name = %(invoice)s")
        params["invoice"] = filters["invoice"]

    # patient filter exists only if field exists
    patient_field = _pick_first_existing_field("Sales Invoice", ["patient", "patient_id"])
    if filters.get("patient") and patient_field:
        where.append(f"si.`{patient_field}` = %(patient)s")
        params["patient"] = filters["patient"]

    doctor_field = _pick_first_existing_field("Sales Invoice", ["ref_practitioner", "practitioner", "doctor"])
    if filters.get("doctor") and doctor_field:
        where.append(f"si.`{doctor_field}` = %(doctor)s")
        params["doctor"] = filters["doctor"]

    if filters.get("created_by"):
        where.append("si.owner = %(created_by)s")
        params["created_by"] = filters["created_by"]

    if filters.get("only_discounted"):
        where.append("(IFNULL(si.discount_amount, 0) > 0 OR IFNULL(si.additional_discount_percentage, 0) > 0)")

    status_filter = (filters.get("status") or "").strip()
    if status_filter == "Cancelled":
        where.append("si.docstatus = 2")
    elif status_filter == "Return":
        where.append("IFNULL(si.is_return, 0) = 1 AND si.docstatus < 2")
    elif status_filter == "Paid":
        where.append("si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.outstanding_amount, 0) = 0")
    elif status_filter == "Credit":
        where.append("si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.outstanding_amount, 0) > 0")

    where_sql = " AND ".join(where)

    # ✅ Discount amount expression (same logic you used in detail)
    discount_amount_expr = """
        CASE
          WHEN IFNULL(si.discount_amount, 0) > 0 THEN IFNULL(si.discount_amount, 0)
          WHEN IFNULL(si.additional_discount_percentage, 0) > 0
               AND (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)) > 0
          THEN ROUND(
                (IFNULL(si.grand_total, 0) / (1 - (IFNULL(si.additional_discount_percentage, 0) / 100)))
                - IFNULL(si.grand_total, 0)
              , 2)
          ELSE 0
        END
    """

    total_before_expr = f"(IFNULL(si.grand_total, 0) + ({discount_amount_expr}))"

    # Needs remark if: Cancelled/Return/Credit/Discounted
    needs_remark_expr = f"""
      (
        si.docstatus = 2
        OR IFNULL(si.is_return, 0) = 1
        OR (si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.outstanding_amount, 0) > 0)
        OR (({discount_amount_expr}) > 0 OR IFNULL(si.additional_discount_percentage, 0) > 0)
      )
    """

    missing_remark_expr = f"""
      (
        {needs_remark_expr}
        AND IFNULL({remark_sql}, '') = ''
      )
    """

    sql = """
      SELECT
        COUNT(*) AS invoice_count,

        SUM({total_before_expr}) AS total_before_discount,
        SUM({discount_amount_expr}) AS total_discount,
        SUM(IFNULL(si.grand_total, 0)) AS grand_total_after_discount,

        SUM(IFNULL(si.grand_total, 0) - IFNULL(si.outstanding_amount, 0)) AS total_paid,
        SUM(IFNULL(si.outstanding_amount, 0)) AS total_outstanding,

        SUM(CASE WHEN si.docstatus = 2 THEN 1 ELSE 0 END) AS cancelled_count,
        SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 AND si.docstatus < 2 THEN 1 ELSE 0 END) AS return_count,
        SUM(CASE WHEN si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.outstanding_amount, 0) > 0 THEN 1 ELSE 0 END) AS credit_count,

        SUM(CASE WHEN {missing_remark_expr} THEN 1 ELSE 0 END) AS missing_remark_count

      FROM `tabSales Invoice` si
      WHERE {where_sql}
    """.format(
        where_sql=where_sql,
        discount_amount_expr=discount_amount_expr,
        total_before_expr=total_before_expr,
        missing_remark_expr=missing_remark_expr,
    )

    r = frappe.db.sql(sql, params, as_dict=True)
    r = (r or [{}])[0]

    def num(x):
        try:
            return float(x or 0)
        except Exception:
            return 0

    def integer(x):
        try:
            return int(x or 0)
        except Exception:
            return 0

    summary = [
        {"label": _("Invoices"), "value": integer(r.get("invoice_count")), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Total (Before Discount)"), "value": num(r.get("total_before_discount")), "indicator": "Blue", "datatype": "Currency"},
        {"label": _("Discount"), "value": num(r.get("total_discount")), "indicator": "Orange", "datatype": "Currency"},
        {"label": _("Grand Total (After Discount)"), "value": num(r.get("grand_total_after_discount")), "indicator": "Blue", "datatype": "Currency"},
        {"label": _("Paid"), "value": num(r.get("total_paid")), "indicator": "Green", "datatype": "Currency"},
        {"label": _("Outstanding"), "value": num(r.get("total_outstanding")), "indicator": "Orange", "datatype": "Currency"},
        {"label": _("Missing Remarks"), "value": integer(r.get("missing_remark_count")), "indicator": "Red" if integer(r.get("missing_remark_count")) > 0 else "Green", "datatype": "Int"},
    ]

    # optional: show these too (useful for daily control)
    summary += [
        {"label": _("Cancelled"), "value": integer(r.get("cancelled_count")), "indicator": "Red", "datatype": "Int"},
        {"label": _("Returns"), "value": integer(r.get("return_count")), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Credit"), "value": integer(r.get("credit_count")), "indicator": "Orange", "datatype": "Int"},
    ]

    return summary
