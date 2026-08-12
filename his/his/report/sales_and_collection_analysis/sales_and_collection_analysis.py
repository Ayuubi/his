# Copyright (c) 2026
# License: MIT

from collections import defaultdict
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import flt, getdate


TODAY_SALES = "Today's Sales"
PREVIOUS_INVOICE = "Previous Invoice"
UNALLOCATED = "Unallocated"


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    currency = frappe.db.get_value(
        "Company", filters.company, "default_currency"
    )

    invoices = get_sales_invoices(filters)
    return_rows = get_sales_return_rows(invoices)

    si_cash_rows, si_settlement_rows = get_sales_invoice_payment_data(filters)
    pe_cash_rows, pe_settlement_rows, discount_rows = get_payment_entry_data(filters)
    je_cash_rows, je_settlement_rows = get_journal_entry_data(filters)

    cash_rows = si_cash_rows + pe_cash_rows + je_cash_rows
    settlement_rows = si_settlement_rows + pe_settlement_rows + je_settlement_rows

    settlement_details = build_sales_settlement_details(
        invoices=invoices,
        settlement_rows=settlement_rows,
        return_rows=return_rows,
    )

    view = filters.view

    if view == "Collection Details":
        filtered_cash_rows = apply_collection_filters(cash_rows, filters)
        columns = get_collection_detail_columns(currency)
        data = sort_collection_rows(filtered_cash_rows)

    elif view in ("Sales Settlement Details", "Not Collected Details"):
        columns = get_settlement_detail_columns(currency)
        data = apply_settlement_filters(settlement_details, filters)

    elif view == "Discount Details":
        columns = get_discount_detail_columns(currency)
        data = apply_discount_filters(discount_rows, filters)

    elif view == "Return Details":
        columns = get_return_detail_columns(currency)
        data = apply_return_filters(return_rows, filters)

    else:
        columns = get_summary_columns(currency)
        data = get_daily_summary(
            filters=filters,
            invoices=invoices,
            cash_rows=cash_rows,
            settlement_details=settlement_details,
        )

    report_summary = get_view_summary(
        filters=filters,
        currency=currency,
        invoices=invoices,
        cash_rows=cash_rows,
        settlement_details=settlement_details,
        discount_rows=discount_rows,
        return_rows=return_rows,
    )

    chart = get_chart(filters, invoices, cash_rows)

    return columns, data, None, chart, report_summary


# =============================================================================
# FILTER VALIDATION
# =============================================================================

def validate_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("Company is required."))

    if not filters.get("from_date"):
        frappe.throw(_("From Date is required."))

    if not filters.get("to_date"):
        frappe.throw(_("To Date is required."))

    filters.from_date = getdate(filters.from_date)
    filters.to_date = getdate(filters.to_date)

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date."))

    filters.view = filters.get("view") or "Daily Summary"


# =============================================================================
# SALES INVOICES AND RETURNS
# =============================================================================

def get_sales_invoices(filters):
    conditions = [
        "si.docstatus = 1",
        "si.company = %(company)s",
        "si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]

    values = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.customer

    if filters.get("customer_group"):
        conditions.append("c.customer_group = %(customer_group)s")
        values["customer_group"] = filters.customer_group

    return frappe.db.sql(
        """
        SELECT
            si.name AS sales_invoice,
            si.posting_date AS invoice_date,
            si.customer,
            si.customer_name,
            si.owner AS created_by,
            COALESCE(si.is_return, 0) AS is_return,
            si.return_against,
            si.voucher_no,
            COALESCE(si.base_grand_total, si.grand_total, 0) AS invoice_total
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c
            ON c.name = si.customer
        WHERE {conditions}
        ORDER BY si.posting_date, si.name
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )


def resolve_original_invoice(invoice):
    return invoice.return_against or invoice.voucher_no


def get_sales_return_rows(invoices):
    rows = []

    for invoice in invoices:
        if not invoice.is_return:
            continue

        original_invoice = resolve_original_invoice(invoice)

        rows.append(
            frappe._dict(
                {
                    "posting_date": getdate(invoice.invoice_date),
                    "sales_return": invoice.sales_invoice,
                    "return_against": invoice.return_against,
                    "voucher_no": invoice.voucher_no,
                    "original_invoice": original_invoice,
                    "customer": invoice.customer,
                    "customer_name": invoice.customer_name,
                    "return_amount": abs(flt(invoice.invoice_total)),
                    "is_linked": 1 if original_invoice else 0,
                    "created_by": invoice.created_by,
                }
            )
        )

    return rows


# =============================================================================
# SALES INVOICE / POS CASH
# =============================================================================

def get_sales_invoice_payment_data(filters):
    conditions = [
        "si.docstatus = 1",
        "si.company = %(company)s",
        "si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "COALESCE(si.is_return, 0) = 0",
        "COALESCE(sip.base_amount, sip.amount, 0) > 0",
    ]

    values = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.customer

    if filters.get("customer_group"):
        conditions.append("c.customer_group = %(customer_group)s")
        values["customer_group"] = filters.customer_group

    rows = frappe.db.sql(
        """
        SELECT
            si.name AS sales_invoice,
            si.posting_date AS collection_date,
            si.posting_date AS invoice_date,
            si.customer,
            si.customer_name,
            si.owner AS collected_by,
            sip.mode_of_payment,
            sip.account AS collection_account,
            COALESCE(sip.base_amount, sip.amount, 0) AS amount
        FROM `tabSales Invoice Payment` sip
        INNER JOIN `tabSales Invoice` si
            ON si.name = sip.parent
        LEFT JOIN `tabCustomer` c
            ON c.name = si.customer
        WHERE {conditions}
        ORDER BY si.posting_date, si.name, sip.idx
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )

    cash_rows = []
    settlement_rows = []

    for row in rows:
        amount = flt(row.amount)
        if amount <= 0:
            continue

        cash_rows.append(
            make_cash_row(
                collection_date=row.collection_date,
                invoice_date=row.invoice_date,
                customer=row.customer,
                customer_name=row.customer_name,
                sales_invoice=row.sales_invoice,
                collection_voucher=row.sales_invoice,
                voucher_type="Sales Invoice",
                mode_of_payment=row.mode_of_payment,
                collection_account=row.collection_account,
                collected_by=row.collected_by,
                classification=TODAY_SALES,
                amount=amount,
            )
        )

        settlement_rows.append(
            make_settlement_row(
                settlement_date=row.collection_date,
                invoice_date=row.invoice_date,
                sales_invoice=row.sales_invoice,
                source_voucher=row.sales_invoice,
                source_type="Sales Invoice",
                cash_amount=amount,
                discount_amount=0,
                other_adjustment_amount=0,
            )
        )

    return cash_rows, settlement_rows


# =============================================================================
# PAYMENT ENTRY CASH AND ACTUAL DEDUCTIONS
# =============================================================================

def get_payment_entry_data(filters):
    conditions = [
        "pe.docstatus = 1",
        "pe.company = %(company)s",
        "pe.payment_type = 'Receive'",
        "pe.party_type = 'Customer'",
        "pe.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]

    values = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("customer"):
        conditions.append("pe.party = %(customer)s")
        values["customer"] = filters.customer

    if filters.get("customer_group"):
        conditions.append("c.customer_group = %(customer_group)s")
        values["customer_group"] = filters.customer_group

    rows = frappe.db.sql(
        """
        SELECT
            pe.name AS payment_entry,
            pe.posting_date AS collection_date,
            pe.party AS customer,
            pe.party_name AS customer_name,
            pe.owner AS collected_by,
            pe.mode_of_payment,
            pe.paid_to AS collection_account,

            COALESCE(
                pe.base_received_amount,
                pe.received_amount,
                0
            ) AS base_received_amount,

            COALESCE(pe.received_amount, 0)
                AS received_amount,

            per.reference_doctype,
            per.reference_name,

            COALESCE(per.outstanding_amount, 0)
                AS outstanding_amount,

            COALESCE(per.allocated_amount, 0)
                AS allocated_amount,

            si.posting_date AS invoice_date,
            COALESCE(si.is_return, 0) AS is_return

        FROM `tabPayment Entry` pe

        LEFT JOIN `tabCustomer` c
            ON c.name = pe.party

        LEFT JOIN `tabPayment Entry Reference` per
            ON per.parent = pe.name

        LEFT JOIN `tabSales Invoice` si
            ON si.name = per.reference_name
            AND per.reference_doctype = 'Sales Invoice'
            AND si.docstatus = 1

        WHERE {conditions}

        ORDER BY
            pe.posting_date,
            pe.name,
            per.idx
        """.format(
            conditions=" AND ".join(conditions)
        ),
        values,
        as_dict=True,
    )

    payment_entries = {}

    for row in rows:
        payment_entry = payment_entries.setdefault(
            row.payment_entry,
            {
                "payment_entry": row.payment_entry,
                "collection_date": getdate(row.collection_date),
                "customer": row.customer,
                "customer_name": row.customer_name,
                "collected_by": row.collected_by,
                "mode_of_payment": row.mode_of_payment,
                "collection_account": row.collection_account,
                "base_received_amount": flt(
                    row.base_received_amount
                ),
                "received_amount": flt(
                    row.received_amount
                ),
                "references": [],
            },
        )

        if row.reference_doctype and row.reference_name:
            payment_entry["references"].append(
                {
                    "reference_doctype": row.reference_doctype,
                    "reference_name": row.reference_name,
                    "invoice_date": (
                        getdate(row.invoice_date)
                        if row.invoice_date
                        else None
                    ),
                    "outstanding_amount": flt(
                        row.outstanding_amount
                    ),
                    "allocated_amount": flt(
                        row.allocated_amount
                    ),
                    "is_return": flt(row.is_return),
                }
            )

    deductions = get_payment_entry_deductions(
        list(payment_entries)
    )

    cash_rows = []
    settlement_rows = []
    discount_rows = []

    for payment_entry in payment_entries.values():
        payment_entry_name = payment_entry[
            "payment_entry"
        ]

        base_received_amount = flt(
            payment_entry["base_received_amount"]
        )

        received_amount = flt(
            payment_entry["received_amount"]
        )

        if base_received_amount <= 0:
            continue

        conversion_factor = (
            base_received_amount / received_amount
            if received_amount
            else 1
        )

        invoice_references = []

        for reference in payment_entry["references"]:
            if (
                reference["reference_doctype"]
                != "Sales Invoice"
            ):
                continue

            if not reference["invoice_date"]:
                continue

            # Returns and negative references are not normal
            # cash/discount allocation targets.
            if (
                reference["is_return"]
                or reference["allocated_amount"] < 0
            ):
                continue

            cash_allocation = flt(
                reference["allocated_amount"]
                * conversion_factor
            )

            outstanding_before = flt(
                reference["outstanding_amount"]
                * conversion_factor
            )

            remaining_after_cash = max(
                outstanding_before - cash_allocation,
                0,
            )

            invoice_references.append(
                {
                    "sales_invoice": reference[
                        "reference_name"
                    ],
                    "invoice_date": reference[
                        "invoice_date"
                    ],
                    "outstanding_before": (
                        outstanding_before
                    ),
                    "cash_allocation": cash_allocation,
                    "discount_basis": (
                        remaining_after_cash
                    ),
                }
            )

        deduction_items = deductions.get(
            payment_entry_name,
            [],
        )

        actual_discount = sum(
            abs(flt(row.amount))
            for row in deduction_items
        )

        total_cash_allocated = sum(
            flt(row["cash_allocation"])
            for row in invoice_references
        )

        total_discount_basis = sum(
            flt(row["discount_basis"])
            for row in invoice_references
        )

        discount_to_allocate = min(
            actual_discount,
            total_discount_basis,
        )

        discount_factor = (
            discount_to_allocate
            / total_discount_basis
            if total_discount_basis
            else 0
        )

        distributed_discount = 0

        eligible_discount_rows = [
            row
            for row in invoice_references
            if row["discount_basis"] > 0
        ]

        for reference in invoice_references:
            cash_share = flt(
                reference["cash_allocation"]
            )

            discount_share = 0

            if reference["discount_basis"] > 0:
                is_last_eligible = (
                    reference
                    is eligible_discount_rows[-1]
                )

                if is_last_eligible:
                    discount_share = flt(
                        discount_to_allocate
                        - distributed_discount
                    )
                else:
                    discount_share = flt(
                        reference["discount_basis"]
                        * discount_factor
                    )

                    distributed_discount += (
                        discount_share
                    )

            classification = classify_collection(
                invoice_date=reference[
                    "invoice_date"
                ],
                collection_date=payment_entry[
                    "collection_date"
                ],
            )

            # Cash stays exactly equal to the PE reference
            # allocated amount.
            if cash_share > 0:
                cash_rows.append(
                    make_cash_row(
                        collection_date=payment_entry[
                            "collection_date"
                        ],
                        invoice_date=reference[
                            "invoice_date"
                        ],
                        customer=payment_entry[
                            "customer"
                        ],
                        customer_name=payment_entry[
                            "customer_name"
                        ],
                        sales_invoice=reference[
                            "sales_invoice"
                        ],
                        collection_voucher=(
                            payment_entry_name
                        ),
                        voucher_type="Payment Entry",
                        mode_of_payment=payment_entry[
                            "mode_of_payment"
                        ],
                        collection_account=payment_entry[
                            "collection_account"
                        ],
                        collected_by=payment_entry[
                            "collected_by"
                        ],
                        classification=classification,
                        amount=cash_share,
                    )
                )

            settlement_rows.append(
                make_settlement_row(
                    settlement_date=payment_entry[
                        "collection_date"
                    ],
                    invoice_date=reference[
                        "invoice_date"
                    ],
                    sales_invoice=reference[
                        "sales_invoice"
                    ],
                    source_voucher=payment_entry_name,
                    source_type="Payment Entry",
                    cash_amount=cash_share,
                    discount_amount=discount_share,
                    other_adjustment_amount=0,
                )
            )

            # Show rows with cash or discount so Finance
            # can inspect the full allocation.
            if cash_share or discount_share:
                discount_rows.append(
                    frappe._dict(
                        {
                            "posting_date": (
                                payment_entry[
                                    "collection_date"
                                ]
                            ),
                            "payment_entry": (
                                payment_entry_name
                            ),
                            "customer": (
                                payment_entry[
                                    "customer"
                                ]
                            ),
                            "customer_name": (
                                payment_entry[
                                    "customer_name"
                                ]
                            ),
                            "sales_invoice": (
                                reference[
                                    "sales_invoice"
                                ]
                            ),
                            "invoice_date": (
                                reference[
                                    "invoice_date"
                                ]
                            ),
                            "invoice_category": (
                                classification
                            ),
                            "outstanding_before": (
                                reference[
                                    "outstanding_before"
                                ]
                            ),
                            "cash_share": cash_share,
                            "remaining_after_cash": (
                                reference[
                                    "discount_basis"
                                ]
                            ),
                            "discount_share": (
                                discount_share
                            ),
                            "payment_entry_discount": (
                                actual_discount
                            ),
                            "discount_accounts": (
                                format_deduction_accounts(
                                    deduction_items
                                )
                            ),
                            "collected_by": (
                                payment_entry[
                                    "collected_by"
                                ]
                            ),
                        }
                    )
                )

        # Actual unallocated customer cash.
        # Discount is not part of this calculation.
        unallocated_cash = flt(
            base_received_amount
            - total_cash_allocated
        )

        if abs(unallocated_cash) < 0.005:
            unallocated_cash = 0

        if unallocated_cash > 0:
            cash_rows.append(
                make_cash_row(
                    collection_date=payment_entry[
                        "collection_date"
                    ],
                    invoice_date=None,
                    customer=payment_entry["customer"],
                    customer_name=payment_entry[
                        "customer_name"
                    ],
                    sales_invoice=None,
                    collection_voucher=(
                        payment_entry_name
                    ),
                    voucher_type="Payment Entry",
                    mode_of_payment=payment_entry[
                        "mode_of_payment"
                    ],
                    collection_account=payment_entry[
                        "collection_account"
                    ],
                    collected_by=payment_entry[
                        "collected_by"
                    ],
                    classification=UNALLOCATED,
                    amount=unallocated_cash,
                )
            )

        unresolved_discount = flt(
            actual_discount
            - discount_to_allocate
        )

        if abs(unresolved_discount) < 0.005:
            unresolved_discount = 0

        if unresolved_discount > 0:
            discount_rows.append(
                frappe._dict(
                    {
                        "posting_date": payment_entry[
                            "collection_date"
                        ],
                        "payment_entry": (
                            payment_entry_name
                        ),
                        "customer": payment_entry[
                            "customer"
                        ],
                        "customer_name": payment_entry[
                            "customer_name"
                        ],
                        "sales_invoice": None,
                        "invoice_date": None,
                        "invoice_category": UNALLOCATED,
                        "outstanding_before": 0,
                        "cash_share": 0,
                        "remaining_after_cash": 0,
                        "discount_share": (
                            unresolved_discount
                        ),
                        "payment_entry_discount": (
                            actual_discount
                        ),
                        "discount_accounts": (
                            format_deduction_accounts(
                                deduction_items
                            )
                        ),
                        "collected_by": payment_entry[
                            "collected_by"
                        ],
                    }
                )
            )

    return cash_rows, settlement_rows, discount_rows

def get_payment_entry_deductions(payment_entries):
    if not payment_entries:
        return {}

    rows = frappe.db.sql(
        """
        SELECT
            ped.parent AS payment_entry,
            ped.account,
            ped.cost_center,
            COALESCE(ped.amount, 0) AS amount
        FROM `tabPayment Entry Deduction` ped
        WHERE ped.parent IN %(payment_entries)s
        ORDER BY ped.parent, ped.idx
        """,
        {"payment_entries": tuple(payment_entries)},
        as_dict=True,
    )

    grouped = defaultdict(list)

    for row in rows:
        grouped[row.payment_entry].append(row)

    return grouped


def format_deduction_accounts(rows):
    return ", ".join(
        "{0}: {1}".format(row.account, flt(row.amount))
        for row in rows
    )


# =============================================================================
# JOURNAL ENTRY CASH AND OTHER ADJUSTMENTS
# =============================================================================

def get_journal_entry_data(filters):
    conditions = [
        "je.docstatus = 1",
        "je.company = %(company)s",
        "je.posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "jea.party_type = 'Customer'",
        "COALESCE(jea.credit, 0) > 0",
    ]

    values = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("customer"):
        conditions.append("jea.party = %(customer)s")
        values["customer"] = filters.customer

    if filters.get("customer_group"):
        conditions.append("c.customer_group = %(customer_group)s")
        values["customer_group"] = filters.customer_group

    customer_rows = frappe.db.sql(
        """
        SELECT
            je.name AS journal_entry,
            je.posting_date AS settlement_date,
            je.owner AS collected_by,
            jea.party AS customer,
            c.customer_name,
            jea.reference_type,
            jea.reference_name,
            COALESCE(jea.credit, 0) AS credit_amount,
            si.posting_date AS invoice_date
        FROM `tabJournal Entry Account` jea
        INNER JOIN `tabJournal Entry` je
            ON je.name = jea.parent
        LEFT JOIN `tabCustomer` c
            ON c.name = jea.party
        LEFT JOIN `tabSales Invoice` si
            ON si.name = jea.reference_name
            AND jea.reference_type = 'Sales Invoice'
            AND si.docstatus = 1
        WHERE {conditions}
        ORDER BY je.posting_date, je.name, jea.idx
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )

    if not customer_rows:
        return [], []

    journal_names = list(
        {row.journal_entry for row in customer_rows}
    )

    debit_rows = frappe.db.sql(
        """
        SELECT
            jea.parent AS journal_entry,
            jea.account,
            COALESCE(jea.debit, 0) AS debit_amount,
            acc.root_type,
            COALESCE(acc.account_type, '') AS account_type
        FROM `tabJournal Entry Account` jea
        INNER JOIN `tabAccount` acc
            ON acc.name = jea.account
        WHERE jea.parent IN %(journal_names)s
          AND COALESCE(jea.debit, 0) > 0
        ORDER BY jea.parent, jea.idx
        """,
        {"journal_names": tuple(journal_names)},
        as_dict=True,
    )

    debits_by_journal = defaultdict(list)

    for row in debit_rows:
        debits_by_journal[row.journal_entry].append(row)

    cash_rows = []
    settlement_rows = []

    for customer_row in customer_rows:
        credit_amount = flt(customer_row.credit_amount)

        if credit_amount <= 0:
            continue

        debits = debits_by_journal.get(
            customer_row.journal_entry, []
        )

        total_debit = sum(
            flt(row.debit_amount)
            for row in debits
        )

        if total_debit <= 0:
            continue

        cash_amount = 0
        other_adjustment = 0
        cash_accounts = []

        for debit in debits:
            share = flt(
                credit_amount
                * flt(debit.debit_amount)
                / total_debit
            )

            is_cash_like = (
                debit.root_type == "Asset"
                and debit.account_type != "Receivable"
            )

            if is_cash_like:
                cash_amount += share
                cash_accounts.append(debit.account)
            else:
                other_adjustment += share

        has_invoice = (
            customer_row.reference_type == "Sales Invoice"
            and customer_row.reference_name
            and customer_row.invoice_date
        )

        if has_invoice:
            invoice_date = getdate(
                customer_row.invoice_date
            )
            classification = classify_collection(
                invoice_date,
                customer_row.settlement_date,
            )

            if cash_amount > 0:
                cash_rows.append(
                    make_cash_row(
                        collection_date=customer_row.settlement_date,
                        invoice_date=invoice_date,
                        customer=customer_row.customer,
                        customer_name=customer_row.customer_name,
                        sales_invoice=customer_row.reference_name,
                        collection_voucher=customer_row.journal_entry,
                        voucher_type="Journal Entry",
                        mode_of_payment=None,
                        collection_account=", ".join(cash_accounts),
                        collected_by=customer_row.collected_by,
                        classification=classification,
                        amount=cash_amount,
                    )
                )

            settlement_rows.append(
                make_settlement_row(
                    settlement_date=customer_row.settlement_date,
                    invoice_date=invoice_date,
                    sales_invoice=customer_row.reference_name,
                    source_voucher=customer_row.journal_entry,
                    source_type="Journal Entry",
                    cash_amount=cash_amount,
                    discount_amount=0,
                    other_adjustment_amount=other_adjustment,
                )
            )

        elif cash_amount > 0:
            cash_rows.append(
                make_cash_row(
                    collection_date=customer_row.settlement_date,
                    invoice_date=None,
                    customer=customer_row.customer,
                    customer_name=customer_row.customer_name,
                    sales_invoice=None,
                    collection_voucher=customer_row.journal_entry,
                    voucher_type="Journal Entry",
                    mode_of_payment=None,
                    collection_account=", ".join(cash_accounts),
                    collected_by=customer_row.collected_by,
                    classification=UNALLOCATED,
                    amount=cash_amount,
                )
            )

    return cash_rows, settlement_rows


# =============================================================================
# SALES SETTLEMENT DETAILS
# =============================================================================

def build_sales_settlement_details(
    invoices,
    settlement_rows,
    return_rows,
):
    invoice_map = {
        row.sales_invoice: row
        for row in invoices
    }

    settlements = defaultdict(
        lambda: {
            "cash": 0,
            "discount": 0,
            "other": 0,
        }
    )

    for row in settlement_rows:
        if not row.sales_invoice:
            continue

        if getdate(row.settlement_date) != getdate(
            row.invoice_date
        ):
            continue

        settlements[row.sales_invoice]["cash"] += flt(
            row.cash_amount
        )
        settlements[row.sales_invoice]["discount"] += flt(
            row.discount_amount
        )
        settlements[row.sales_invoice]["other"] += flt(
            row.other_adjustment_amount
        )

    returns_by_original = defaultdict(float)
    return_names_by_original = defaultdict(list)

    for row in return_rows:
        original_invoice_name = row.original_invoice

        if not original_invoice_name:
            continue

        original = invoice_map.get(
            original_invoice_name
        )

        if not original:
            continue

        if getdate(row.posting_date) != getdate(
            original.invoice_date
        ):
            continue

        returns_by_original[
            original_invoice_name
        ] += flt(row.return_amount)

        return_names_by_original[
            original_invoice_name
        ].append(row.sales_return)

    data = []

    for invoice in invoices:
        if invoice.is_return:
            continue

        item = settlements.get(
            invoice.sales_invoice, {}
        )

        invoice_total = flt(invoice.invoice_total)
        cash = flt(item.get("cash"))
        discount = flt(item.get("discount"))
        other = flt(item.get("other"))
        return_credit = flt(
            returns_by_original.get(
                invoice.sales_invoice
            )
        )

        total_settled = flt(
            cash
            + discount
            + other
            + return_credit
        )

        outstanding = flt(
            invoice_total - total_settled
        )

        if abs(outstanding) < 0.005:
            outstanding = 0

        data.append(
            {
                "invoice_date": invoice.invoice_date,
                "sales_invoice": invoice.sales_invoice,
                "customer": invoice.customer,
                "customer_name": invoice.customer_name,
                "invoice_total": invoice_total,
                "cash_collected": cash,
                "discount_settlement": discount,
                "other_adjustment": other,
                "return_credit": return_credit,
                "return_invoices": ", ".join(
                    return_names_by_original.get(
                        invoice.sales_invoice, []
                    )
                ),
                "total_settled": total_settled,
                "outstanding_at_day_end": outstanding,
                "created_by": invoice.created_by,
            }
        )

    return data


# =============================================================================
# HELPERS AND FILTERS
# =============================================================================

def classify_collection(invoice_date, collection_date):
    invoice_date = getdate(invoice_date)
    collection_date = getdate(collection_date)

    if invoice_date == collection_date:
        return TODAY_SALES

    if invoice_date < collection_date:
        return PREVIOUS_INVOICE

    return UNALLOCATED


def make_cash_row(
    collection_date,
    invoice_date,
    customer,
    customer_name,
    sales_invoice,
    collection_voucher,
    voucher_type,
    mode_of_payment,
    collection_account,
    collected_by,
    classification,
    amount,
):
    return frappe._dict(
        {
            "collection_date": getdate(
                collection_date
            ),
            "invoice_date": (
                getdate(invoice_date)
                if invoice_date
                else None
            ),
            "customer": customer,
            "customer_name": customer_name,
            "sales_invoice": sales_invoice,
            "collection_voucher": collection_voucher,
            "voucher_type": voucher_type,
            "mode_of_payment": mode_of_payment,
            "collection_account": collection_account,
            "collected_by": collected_by,
            "classification": classification,
            "amount": flt(amount),
        }
    )


def make_settlement_row(
    settlement_date,
    invoice_date,
    sales_invoice,
    source_voucher,
    source_type,
    cash_amount,
    discount_amount,
    other_adjustment_amount,
):
    return frappe._dict(
        {
            "settlement_date": getdate(
                settlement_date
            ),
            "invoice_date": getdate(invoice_date),
            "sales_invoice": sales_invoice,
            "source_voucher": source_voucher,
            "source_type": source_type,
            "cash_amount": flt(cash_amount),
            "discount_amount": flt(
                discount_amount
            ),
            "other_adjustment_amount": flt(
                other_adjustment_amount
            ),
        }
    )


def apply_collection_filters(rows, filters):
    filtered = []

    for row in rows:
        if (
            filters.get("classification")
            not in (None, "", "All")
            and row.classification
            != filters.classification
        ):
            continue

        if (
            filters.get("mode_of_payment")
            and row.mode_of_payment
            != filters.mode_of_payment
        ):
            continue

        if (
            filters.get("collection_account")
            and row.collection_account
            != filters.collection_account
        ):
            continue

        if (
            filters.get("collected_by")
            and row.collected_by
            != filters.collected_by
        ):
            continue

        if filters.get("payment_entry"):
            if (
                row.voucher_type != "Payment Entry"
                or row.collection_voucher
                != filters.payment_entry
            ):
                continue

        filtered.append(row)

    return filtered


def apply_settlement_filters(rows, filters):
    filtered = []

    for row in rows:
        if (
            filters.get("sales_invoice")
            and row.get("sales_invoice")
            != filters.sales_invoice
        ):
            continue

        settlement_filter = filters.get(
            "settlement_filter"
        )

        if (
            settlement_filter == "Outstanding Only"
            and flt(
                row.get(
                    "outstanding_at_day_end"
                )
            )
            <= 0
        ):
            continue

        if (
            settlement_filter == "Discounted Only"
            and flt(
                row.get("discount_settlement")
            )
            <= 0
        ):
            continue

        if (
            settlement_filter == "Returned Only"
            and flt(row.get("return_credit"))
            <= 0
        ):
            continue

        filtered.append(row)

    return filtered


def apply_discount_filters(rows, filters):
    filtered = []

    for row in rows:
        if (
            filters.get("payment_entry")
            and row.payment_entry
            != filters.payment_entry
        ):
            continue

        if (
            filters.get("sales_invoice")
            and row.sales_invoice
            != filters.sales_invoice
        ):
            continue

        if (
            filters.get("discount_category")
            not in (None, "", "All")
            and row.invoice_category
            != filters.discount_category
        ):
            continue

        filtered.append(row)

    return filtered


def apply_return_filters(rows, filters):
    filtered = []

    for row in rows:
        if filters.get("sales_invoice"):
            if (
                row.sales_return
                != filters.sales_invoice
                and row.original_invoice
                != filters.sales_invoice
            ):
                continue

        if (
            filters.get("return_link_status")
            == "Linked Only"
            and not row.is_linked
        ):
            continue

        if (
            filters.get("return_link_status")
            == "Unlinked Only"
            and row.is_linked
        ):
            continue

        filtered.append(row)

    return filtered


def sort_collection_rows(rows):
    rows.sort(
        key=lambda row: (
            row.collection_date,
            row.voucher_type or "",
            row.collection_voucher or "",
            row.sales_invoice or "",
        )
    )
    return rows


# =============================================================================
# DAILY SUMMARY
# =============================================================================

def get_daily_summary(
    filters,
    invoices,
    cash_rows,
    settlement_details,
):
    gross_sales_by_date = defaultdict(float)
    returns_by_date = defaultdict(float)

    for invoice in invoices:
        posting_date = getdate(
            invoice.invoice_date
        )

        if invoice.is_return:
            returns_by_date[
                posting_date
            ] += abs(flt(invoice.invoice_total))
        else:
            gross_sales_by_date[
                posting_date
            ] += flt(invoice.invoice_total)

    settlement_by_date = defaultdict(
        lambda: {
            "cash": 0,
            "outstanding": 0,
        }
    )

    for row in settlement_details:
        invoice_date = getdate(
            row.get("invoice_date")
        )

        settlement_by_date[
            invoice_date
        ]["cash"] += flt(
            row.get("cash_collected")
        )

        settlement_by_date[
            invoice_date
        ]["outstanding"] += flt(
            row.get("outstanding_at_day_end")
        )

    cash_by_date = defaultdict(
        lambda: {
            TODAY_SALES: 0,
            PREVIOUS_INVOICE: 0,
            UNALLOCATED: 0,
        }
    )

    for row in cash_rows:
        cash_by_date[
            getdate(row.collection_date)
        ][row.classification] += flt(
            row.amount
        )

    data = []
    current_date = filters.from_date

    while current_date <= filters.to_date:
        gross_sales = flt(
            gross_sales_by_date.get(
                current_date
            )
        )

        sales_returns = flt(
            returns_by_date.get(current_date)
        )

        net_sales = flt(
            gross_sales - sales_returns
        )

        cash_from_today_sales = flt(
            settlement_by_date[
                current_date
            ]["cash"]
        )

        cash_from_previous = flt(
            cash_by_date[
                current_date
            ][PREVIOUS_INVOICE]
        )

        unallocated_cash = flt(
            cash_by_date[
                current_date
            ][UNALLOCATED]
        )

        outstanding_from_today_sales = flt(
            settlement_by_date[
                current_date
            ]["outstanding"]
        )

        total_cash_collected = flt(
            cash_from_today_sales
            + cash_from_previous
            + unallocated_cash
        )

        data.append(
            {
                "posting_date": current_date,
                "net_sales": net_sales,
                "cash_from_today_sales": (
                    cash_from_today_sales
                ),
                "cash_from_previous_invoices": (
                    cash_from_previous
                ),
                "unallocated_cash": (
                    unallocated_cash
                ),
                "outstanding_from_today_sales": (
                    outstanding_from_today_sales
                ),
                "total_cash_collected": (
                    total_cash_collected
                ),
            }
        )

        current_date += timedelta(days=1)

    if len(data) > 1:
        total = {
            "posting_date": None,
            "is_total_row": 1,
        }

        for fieldname in (
            "net_sales",
            "cash_from_today_sales",
            "cash_from_previous_invoices",
            "unallocated_cash",
            "outstanding_from_today_sales",
            "total_cash_collected",
        ):
            total[fieldname] = sum(
                flt(row.get(fieldname))
                for row in data
            )

        data.append(total)

    return data


# =============================================================================
# VIEW-SPECIFIC SUMMARY CARDS
# =============================================================================

def get_view_summary(
    filters,
    currency,
    invoices,
    cash_rows,
    settlement_details,
    discount_rows,
    return_rows,
):
    view = filters.view

    if view == "Collection Details":
        today_cash = sum(
            flt(row.amount)
            for row in cash_rows
            if row.classification == TODAY_SALES
        )
        previous_cash = sum(
            flt(row.amount)
            for row in cash_rows
            if row.classification
            == PREVIOUS_INVOICE
        )
        unallocated_cash = sum(
            flt(row.amount)
            for row in cash_rows
            if row.classification == UNALLOCATED
        )
        total_cash = flt(
            today_cash
            + previous_cash
            + unallocated_cash
        )

        return [
            summary_card(
                "Cash From Today's Sales",
                today_cash,
                "Green",
                currency,
            ),
            summary_card(
                "Cash From Previous Invoices",
                previous_cash,
                "Blue",
                currency,
            ),
            summary_card(
                "Unallocated Cash",
                unallocated_cash,
                "Orange",
                currency,
            ),
            summary_card(
                "Total Cash Collected",
                total_cash,
                "Green",
                currency,
            ),
        ]

    if view in (
        "Sales Settlement Details",
        "Not Collected Details",
    ):
        sales_before_returns = sum(
            flt(row.invoice_total)
            for row in invoices
            if not row.is_return
        )
        returns_today = sum(
            flt(row.return_amount)
            for row in return_rows
        )
        discounts_today_sales = sum(
            flt(
                row.get(
                    "discount_settlement"
                )
            )
            for row in settlement_details
        )
        outstanding_today = sum(
            flt(
                row.get(
                    "outstanding_at_day_end"
                )
            )
            for row in settlement_details
        )

        return [
            summary_card(
                "Sales Before Returns",
                sales_before_returns,
                "Blue",
                currency,
            ),
            summary_card(
                "Returns Today",
                returns_today,
                "Orange",
                currency,
            ),
            summary_card(
                "Discounts on Today's Sales",
                discounts_today_sales,
                "Orange",
                currency,
            ),
            summary_card(
                "Outstanding From Today's Sales",
                outstanding_today,
                "Red",
                currency,
            ),
        ]

    if view == "Discount Details":
        payment_entry_totals = {}

        same_day_discount = 0
        previous_discount = 0
        unresolved_discount = 0

        for row in discount_rows:
            payment_entry_totals[
                row.payment_entry
            ] = flt(
                row.payment_entry_discount
            )

            if (
                row.invoice_category
                == TODAY_SALES
            ):
                same_day_discount += flt(
                    row.discount_share
                )
            elif (
                row.invoice_category
                == PREVIOUS_INVOICE
            ):
                previous_discount += flt(
                    row.discount_share
                )
            else:
                unresolved_discount += flt(
                    row.discount_share
                )

        total_discounts = sum(
            payment_entry_totals.values()
        )

        return [
            summary_card(
                "Total Discounts Processed",
                total_discounts,
                "Orange",
                currency,
            ),
            summary_card(
                "Discounts on Today's Sales",
                same_day_discount,
                "Blue",
                currency,
            ),
            summary_card(
                "Discounts on Previous Invoices",
                previous_discount,
                "Blue",
                currency,
            ),
            summary_card(
                "Unresolved Discount",
                unresolved_discount,
                "Red"
                if unresolved_discount
                else "Green",
                currency,
            ),
        ]

    if view == "Return Details":
        total_returns = sum(
            flt(row.return_amount)
            for row in return_rows
        )
        linked_returns = sum(
            flt(row.return_amount)
            for row in return_rows
            if row.is_linked
        )
        unlinked_returns = sum(
            flt(row.return_amount)
            for row in return_rows
            if not row.is_linked
        )

        return [
            summary_card(
                "Total Returns",
                total_returns,
                "Orange",
                currency,
            ),
            summary_card(
                "Linked Returns",
                linked_returns,
                "Green",
                currency,
            ),
            summary_card(
                "Unlinked Returns",
                unlinked_returns,
                "Red"
                if unlinked_returns
                else "Green",
                currency,
            ),
        ]

    net_sales = (
        sum(
            flt(row.invoice_total)
            for row in invoices
            if not row.is_return
        )
        - sum(
            abs(flt(row.invoice_total))
            for row in invoices
            if row.is_return
        )
    )

    cash_from_today_sales = sum(
        flt(row.amount)
        for row in cash_rows
        if row.classification == TODAY_SALES
    )

    cash_from_previous = sum(
        flt(row.amount)
        for row in cash_rows
        if row.classification
        == PREVIOUS_INVOICE
    )

    unallocated_cash = sum(
        flt(row.amount)
        for row in cash_rows
        if row.classification == UNALLOCATED
    )

    outstanding_today = sum(
        flt(
            row.get(
                "outstanding_at_day_end"
            )
        )
        for row in settlement_details
    )

    total_cash = flt(
        cash_from_today_sales
        + cash_from_previous
        + unallocated_cash
    )

    return [
        summary_card(
            "Net Sales",
            net_sales,
            "Blue",
            currency,
        ),
        summary_card(
            "Cash From Today's Sales",
            cash_from_today_sales,
            "Green",
            currency,
        ),
        summary_card(
            "Cash From Previous Invoices",
            cash_from_previous,
            "Blue",
            currency,
        ),
        summary_card(
            "Outstanding From Today's Sales",
            outstanding_today,
            "Red",
            currency,
        ),
        summary_card(
            "Total Cash Collected",
            total_cash,
            "Green",
            currency,
        ),
    ]


def summary_card(
    label,
    value,
    indicator,
    currency,
):
    return {
        "value": flt(value),
        "indicator": indicator,
        "label": _(label),
        "datatype": "Currency",
        "currency": currency,
    }


# =============================================================================
# COLUMNS
# =============================================================================

def currency_column(
    label,
    fieldname,
    currency,
    width=140,
):
    return {
        "label": _(label),
        "fieldname": fieldname,
        "fieldtype": "Currency",
        "options": currency,
        "width": width,
    }


def get_summary_columns(currency):
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 105,
        },
        currency_column(
            "Net Sales",
            "net_sales",
            currency,
        ),
        currency_column(
            "Cash From Today's Sales",
            "cash_from_today_sales",
            currency,
            185,
        ),
        currency_column(
            "Cash From Previous Invoices",
            "cash_from_previous_invoices",
            currency,
            210,
        ),
        currency_column(
            "Unallocated Cash",
            "unallocated_cash",
            currency,
            150,
        ),
        currency_column(
            "Outstanding From Today's Sales",
            "outstanding_from_today_sales",
            currency,
            215,
        ),
        currency_column(
            "Total Cash Collected",
            "total_cash_collected",
            currency,
            175,
        ),
    ]


def get_collection_detail_columns(currency):
    return [
        {
            "label": _("Collection Date"),
            "fieldname": "collection_date",
            "fieldtype": "Date",
            "width": 115,
        },
        {
            "label": _("Invoice Date"),
            "fieldname": "invoice_date",
            "fieldtype": "Date",
            "width": 105,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 190,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Collection Voucher"),
            "fieldname": "collection_voucher",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180,
        },
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 125,
        },
        {
            "label": _("Mode of Payment"),
            "fieldname": "mode_of_payment",
            "fieldtype": "Link",
            "options": "Mode of Payment",
            "width": 170,
        },
        {
            "label": _("Collection Account"),
            "fieldname": "collection_account",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Collected By"),
            "fieldname": "collected_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
        {
            "label": _("Cash Source"),
            "fieldname": "classification",
            "fieldtype": "Data",
            "width": 150,
        },
        currency_column(
            "Cash Amount",
            "amount",
            currency,
            135,
        ),
    ]


def get_settlement_detail_columns(currency):
    return [
        {
            "label": _("Invoice Date"),
            "fieldname": "invoice_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 190,
        },
        currency_column(
            "Invoice Amount",
            "invoice_total",
            currency,
        ),
        currency_column(
            "Cash Received",
            "cash_collected",
            currency,
        ),
        currency_column(
            "Discount",
            "discount_settlement",
            currency,
        ),
        currency_column(
            "Return Credit",
            "return_credit",
            currency,
        ),
        currency_column(
            "Other Adjustment",
            "other_adjustment",
            currency,
            150,
        ),
        currency_column(
            "Outstanding",
            "outstanding_at_day_end",
            currency,
            145,
        ),
        {
            "label": _("Return Invoices"),
            "fieldname": "return_invoices",
            "fieldtype": "Data",
            "width": 210,
        },
        {
            "label": _("Created By"),
            "fieldname": "created_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
    ]


def get_discount_detail_columns(currency):
    return [
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Payment Entry"),
            "fieldname": "payment_entry",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 180,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Invoice Date"),
            "fieldname": "invoice_date",
            "fieldtype": "Date",
            "width": 105,
        },
        {
            "label": _("Invoice Category"),
            "fieldname": "invoice_category",
            "fieldtype": "Data",
            "width": 145,
        },
        currency_column(
            "Payment Entry Discount",
            "payment_entry_discount",
            currency,
            170,
        ),
        currency_column(
            "Outstanding Before Payment",
            "outstanding_before",
            currency,
            185,
        ),
        currency_column(
            "Cash Applied",
            "cash_share",
            currency,
            135,
        ),
        currency_column(
            "Remaining After Cash",
            "remaining_after_cash",
            currency,
            165,
        ),
        currency_column(
            "Discount Applied",
            "discount_share",
            currency,
            145,
        ),
        {
            "label": _("Discount Accounts"),
            "fieldname": "discount_accounts",
            "fieldtype": "Data",
            "width": 260,
        },
        {
            "label": _("Collected By"),
            "fieldname": "collected_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
    ]

def get_return_detail_columns(currency):
    return [
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Sales Return"),
            "fieldname": "sales_return",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Return Against"),
            "fieldname": "return_against",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Original Invoice"),
            "fieldname": "original_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 190,
        },
        currency_column(
            "Return Amount",
            "return_amount",
            currency,
            140,
        ),
        {
            "label": _("Linked"),
            "fieldname": "is_linked",
            "fieldtype": "Check",
            "width": 80,
        },
        {
            "label": _("Created By"),
            "fieldname": "created_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
    ]


# =============================================================================
# CHART
# =============================================================================

def get_chart(filters, invoices, cash_rows):
    if filters.view != "Daily Summary":
        return None

    net_sales_by_date = defaultdict(float)
    cash_by_date = defaultdict(float)

    for invoice in invoices:
        net_sales_by_date[
            getdate(invoice.invoice_date)
        ] += flt(invoice.invoice_total)

    for row in cash_rows:
        cash_by_date[
            getdate(row.collection_date)
        ] += flt(row.amount)

    labels = []
    net_sales_values = []
    cash_values = []

    current_date = filters.from_date

    while current_date <= filters.to_date:
        labels.append(
            current_date.strftime("%d-%b")
        )
        net_sales_values.append(
            flt(
                net_sales_by_date.get(
                    current_date
                )
            )
        )
        cash_values.append(
            flt(
                cash_by_date.get(current_date)
            )
        )
        current_date += timedelta(days=1)

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Net Sales"),
                    "values": net_sales_values,
                },
                {
                    "name": _(
                        "Total Cash Collected"
                    ),
                    "values": cash_values,
                },
            ],
        },
        "type": "bar",
        "height": 280,
    }
