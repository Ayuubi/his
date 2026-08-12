# Copyright (c) 2026, Rasiin Tech
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate


TOLERANCE = 0.01


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    accounts = get_reconciliation_accounts(
        company=filters.company,
        main_merchant_account=filters.main_merchant_account,
    )

    merchant_accounts = accounts["merchant_accounts"]
    main_merchant_account = accounts["main_merchant_account"]
    bank_accounts = accounts["bank_accounts"]
    all_accounts = accounts["all_accounts"]
    account_details = accounts["account_details"]

    opening_balances = get_opening_balances(
        company=filters.company,
        from_date=filters.from_date,
        accounts=all_accounts,
    )

    gl_entries = get_gl_entries(
        company=filters.company,
        from_date=filters.from_date,
        to_date=filters.to_date,
        accounts=all_accounts,
    )

    voucher_information = get_voucher_information(gl_entries)

    mode_of_payment_by_account = get_mode_of_payment_by_account(
        filters.company
    )

    movements = analyse_gl_entries(
        gl_entries=gl_entries,
        merchant_accounts=set(merchant_accounts),
        main_merchant_account=main_merchant_account,
        bank_accounts=set(bank_accounts),
        voucher_information=voucher_information,
        mode_of_payment_by_account=mode_of_payment_by_account,
    )

    data = build_report_rows(
        filters=filters,
        merchant_accounts=merchant_accounts,
        main_merchant_account=main_merchant_account,
        bank_accounts=bank_accounts,
        account_details=account_details,
        opening_balances=opening_balances,
        movements=movements,
    )

    data = apply_report_filters(data, filters)

    return (
        get_columns(),
        data,
        None,
        build_chart(data),
        build_report_summary(data),
    )


# =============================================================================
# VALIDATION
# =============================================================================


def validate_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("Company is required."))

    if not filters.get("from_date"):
        frappe.throw(_("From Date is required."))

    if not filters.get("to_date"):
        frappe.throw(_("To Date is required."))

    if not filters.get("main_merchant_account"):
        frappe.throw(
            _(
                "Please select the final Main Merchant Account. "
                "All other Cash and Bank accounts will be loaded automatically."
            )
        )

    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be after To Date."))

    account = frappe.db.get_value(
        "Account",
        filters.main_merchant_account,
        [
            "company",
            "is_group",
            "account_type",
        ],
        as_dict=True,
    )

    if not account:
        frappe.throw(_("The selected Main Merchant Account does not exist."))

    if account.company != filters.company:
        frappe.throw(
            _("The Main Merchant Account must belong to the selected company.")
        )

    if cint(account.is_group):
        frappe.throw(_("The Main Merchant Account cannot be a group account."))

    if account.account_type not in ("Cash", "Bank"):
        frappe.throw(
            _(
                "The Main Merchant Account must have Account Type "
                "Cash or Bank."
            )
        )


# =============================================================================
# COLUMNS
# =============================================================================


def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 105,
        },
        {
            "label": _("Account Role"),
            "fieldname": "account_role",
            "fieldtype": "Data",
            "width": 155,
        },
        {
            "label": _("Account"),
            "fieldname": "account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 245,
        },
        {
            "label": _("Account Type"),
            "fieldname": "account_type",
            "fieldtype": "Data",
            "width": 105,
        },
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Data",
            "width": 190,
        },
        {
            "label": _("Mode of Payment"),
            "fieldname": "mode_of_payment",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Opening Balance"),
            "fieldname": "opening_balance",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Daily Collections"),
            "fieldname": "collections",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Refunds / Reversals"),
            "fieldname": "refunds",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Net Collections"),
            "fieldname": "net_collections",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Received from Merchants"),
            "fieldname": "received_from_merchants",
            "fieldtype": "Currency",
            "width": 165,
        },
        {
            "label": _("Merchant Consolidation In"),
            "fieldname": "merchant_transfer_in",
            "fieldtype": "Currency",
            "width": 165,
        },
        {
            "label": _("Other Inflows"),
            "fieldname": "other_inflows",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Available Balance"),
            "fieldname": "available_balance",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Transferred to Main"),
            "fieldname": "transferred_to_main",
            "fieldtype": "Currency",
            "width": 145,
        },
        {
            "label": _("Merchant Consolidation Out"),
            "fieldname": "merchant_transfer_out",
            "fieldtype": "Currency",
            "width": 170,
        },
        {
            "label": _("Transferred to Bank"),
            "fieldname": "transferred_to_bank",
            "fieldtype": "Currency",
            "width": 145,
        },
        {
            "label": _("Other Outflows"),
            "fieldname": "other_outflows",
            "fieldtype": "Currency",
            "width": 125,
        },
        {
            "label": _("Closing Balance"),
            "fieldname": "closing_balance",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Expected Transfer"),
            "fieldname": "expected_transfer",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Actual Transfer"),
            "fieldname": "actual_transfer",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Pending Transfer"),
            "fieldname": "pending_transfer",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Excess Transfer"),
            "fieldname": "excess_transfer",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Transfer Variance"),
            "fieldname": "transfer_variance",
            "fieldtype": "Currency",
            "width": 135,
        },
        {
            "label": _("Received From"),
            "fieldname": "received_from",
            "fieldtype": "Data",
            "width": 230,
        },
        {
            "label": _("Transferred To"),
            "fieldname": "transferred_to",
            "fieldtype": "Data",
            "width": 230,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 155,
        },
        {
            "label": _("Transactions"),
            "fieldname": "transaction_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": _("Reference"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180,
        },
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "hidden": 1,
        },
        {
            "label": _("Remarks"),
            "fieldname": "remarks",
            "fieldtype": "Data",
            "width": 260,
        },
    ]


# =============================================================================
# ACCOUNT DISCOVERY
# =============================================================================


def get_reconciliation_accounts(company, main_merchant_account):
    rows = frappe.get_all(
        "Account",
        filters={
            "company": company,
            "is_group": 0,
            "disabled": 0,
            "account_type": ["in", ["Cash", "Bank"]],
        },
        fields=[
            "name",
            "account_name",
            "account_type",
            "account_currency",
            "root_type",
        ],
        order_by="account_type, account_name",
    )

    account_details = {
        row.name: frappe._dict(row)
        for row in rows
    }

    if main_merchant_account not in account_details:
        main_row = frappe.db.get_value(
            "Account",
            main_merchant_account,
            [
                "name",
                "account_name",
                "account_type",
                "account_currency",
                "root_type",
            ],
            as_dict=True,
        )

        if main_row:
            account_details[main_row.name] = frappe._dict(main_row)

    bank_accounts = [
        row.name
        for row in rows
        if row.account_type == "Bank"
        and row.name != main_merchant_account
    ]

    merchant_accounts = [
        row.name
        for row in rows
        if row.account_type == "Cash"
        and row.name != main_merchant_account
    ]

    all_accounts = unique_list(
        merchant_accounts
        + [main_merchant_account]
        + bank_accounts
    )

    return {
        "merchant_accounts": merchant_accounts,
        "main_merchant_account": main_merchant_account,
        "bank_accounts": bank_accounts,
        "all_accounts": all_accounts,
        "account_details": account_details,
    }


def get_mode_of_payment_by_account(company):
    """
    Maps the default Cash/Bank account configured in Mode of Payment
    to its Mode of Payment name.

    This avoids depending on version-specific fields such as:
    - Sales Invoice.mode_of_payment
    - POS Invoice Payment
    """
    result = defaultdict(set)

    if not frappe.db.exists("DocType", "Mode of Payment Account"):
        return result

    rows = frappe.get_all(
        "Mode of Payment Account",
        filters={"company": company},
        fields=[
            "parent",
            "default_account",
        ],
    )

    for row in rows:
        if row.default_account and row.parent:
            result[row.default_account].add(row.parent)

    return result


# =============================================================================
# OPENING BALANCES AND GL
# =============================================================================


def get_opening_balances(company, from_date, accounts):
    if not accounts:
        return {}

    placeholders = ", ".join(["%s"] * len(accounts))

    query = """
        SELECT
            gle.account,
            SUM(gle.debit - gle.credit) AS opening_balance
        FROM `tabGL Entry` gle
        WHERE
            gle.company = %s
            AND gle.posting_date < %s
            AND gle.is_cancelled = 0
            AND gle.account IN ({accounts})
        GROUP BY gle.account
    """.format(accounts=placeholders)

    values = [company, from_date] + list(accounts)

    result = {
        account: 0.0
        for account in accounts
    }

    for row in frappe.db.sql(query, values, as_dict=True):
        result[row.account] = flt(row.opening_balance)

    return result


def get_gl_entries(company, from_date, to_date, accounts):
    if not accounts:
        return []

    placeholders = ", ".join(["%s"] * len(accounts))

    query = """
        SELECT
            gle.name,
            gle.posting_date,
            gle.account,
            gle.debit,
            gle.credit,
            gle.voucher_type,
            gle.voucher_no,
            gle.against,
            gle.remarks,
            gle.owner,
            gle.creation
        FROM `tabGL Entry` gle
        WHERE
            gle.company = %s
            AND gle.posting_date BETWEEN %s AND %s
            AND gle.is_cancelled = 0
            AND gle.account IN ({accounts})
        ORDER BY
            gle.posting_date,
            gle.voucher_type,
            gle.voucher_no,
            gle.account,
            gle.name
    """.format(accounts=placeholders)

    values = (
        [company, from_date, to_date]
        + list(accounts)
    )

    return frappe.db.sql(query, values, as_dict=True)


# =============================================================================
# VOUCHER INFORMATION
# =============================================================================


def get_voucher_information(gl_entries):
    """
    Fetches voucher owner and Payment Entry mode of payment separately.

    This avoids SQL joins against tables or columns that may not exist
    in a customized ERPNext installation.
    """
    voucher_names = defaultdict(set)

    for row in gl_entries:
        if row.voucher_type and row.voucher_no:
            voucher_names[row.voucher_type].add(row.voucher_no)

    result = {}

    supported_doctypes = [
        "Sales Invoice",
        "POS Invoice",
        "Payment Entry",
        "Journal Entry",
        "Cash Transfer",
    ]

    for doctype in supported_doctypes:
        names = list(voucher_names.get(doctype) or [])

        if not names:
            continue

        if not frappe.db.exists("DocType", doctype):
            continue

        fields = ["name", "owner"]

        if (
            doctype == "Payment Entry"
            and frappe.get_meta(doctype).has_field("mode_of_payment")
        ):
            fields.append("mode_of_payment")

        rows = frappe.get_all(
            doctype,
            filters={"name": ["in", names]},
            fields=fields,
            limit_page_length=0,
        )

        for row in rows:
            key = (doctype, row.name)

            result[key] = {
                "user": row.get("owner"),
                "mode_of_payment": row.get("mode_of_payment"),
            }

    return result


# =============================================================================
# MOVEMENT ANALYSIS
# =============================================================================


def analyse_gl_entries(
    gl_entries,
    merchant_accounts,
    main_merchant_account,
    bank_accounts,
    voucher_information,
    mode_of_payment_by_account,
):
    grouped = group_entries_by_voucher(gl_entries)
    movements = defaultdict(new_movement_bucket)

    for voucher_key, rows in grouped.items():
        posting_date, voucher_type, voucher_no = voucher_key

        voucher_info = voucher_information.get(
            (voucher_type, voucher_no),
            {},
        )

        transaction_user = (
            voucher_info.get("user")
            or first_value(rows, "owner")
        )

        voucher_mode = voucher_info.get("mode_of_payment")

        merchant_debits = [
            row
            for row in rows
            if row.account in merchant_accounts
            and flt(row.debit) > TOLERANCE
        ]

        merchant_credits = [
            row
            for row in rows
            if row.account in merchant_accounts
            and flt(row.credit) > TOLERANCE
        ]

        main_debits = [
            row
            for row in rows
            if row.account == main_merchant_account
            and flt(row.debit) > TOLERANCE
        ]

        main_credits = [
            row
            for row in rows
            if row.account == main_merchant_account
            and flt(row.credit) > TOLERANCE
        ]

        bank_debits = [
            row
            for row in rows
            if row.account in bank_accounts
            and flt(row.debit) > TOLERANCE
        ]

        bank_credits = [
            row
            for row in rows
            if row.account in bank_accounts
            and flt(row.credit) > TOLERANCE
        ]

        has_merchant_to_main = bool(
            merchant_credits and main_debits
        )

        has_main_to_bank = bool(
            main_credits and bank_debits
        )

        has_merchant_to_merchant = bool(
            merchant_debits
            and merchant_credits
            and not main_debits
            and not main_credits
        )

        has_main_to_merchant = bool(
            main_credits and merchant_debits
        )

        # ---------------------------------------------------------------------
        # MERCHANT ACCOUNT ROWS
        # ---------------------------------------------------------------------
        for row in rows:
            if row.account not in merchant_accounts:
                continue

            bucket = movements[(posting_date, row.account)]
            update_bucket_metadata(
                bucket=bucket,
                posting_date=posting_date,
                account=row.account,
                voucher_type=voucher_type,
                voucher_no=voucher_no,
                transaction_user=transaction_user,
                voucher_mode=voucher_mode,
                account_modes=mode_of_payment_by_account.get(
                    row.account
                ),
                remarks=row.remarks,
            )

            debit = flt(row.debit)
            credit = flt(row.credit)

            if has_merchant_to_main:
                if credit > TOLERANCE:
                    bucket["transferred_to_main"] += credit
                    bucket["transferred_to"].add(
                        main_merchant_account
                    )

                if debit > TOLERANCE:
                    bucket["other_inflows"] += debit

                continue

            if has_main_to_merchant:
                if debit > TOLERANCE:
                    bucket["merchant_transfer_in"] += debit
                    bucket["received_from"].add(
                        main_merchant_account
                    )

                if credit > TOLERANCE:
                    bucket["other_outflows"] += credit

                continue

            if has_merchant_to_merchant:
                if debit > TOLERANCE:
                    bucket["merchant_transfer_in"] += debit

                    for source in merchant_credits:
                        if source.account != row.account:
                            bucket["received_from"].add(
                                source.account
                            )

                if credit > TOLERANCE:
                    bucket["merchant_transfer_out"] += credit

                    for destination in merchant_debits:
                        if destination.account != row.account:
                            bucket["transferred_to"].add(
                                destination.account
                            )

                continue

            # No tracked Cash/Bank counterpart:
            # this is external collection, refund, or adjustment.
            if debit > TOLERANCE:
                bucket["collections"] += debit

            if credit > TOLERANCE:
                bucket["refunds"] += credit

        # ---------------------------------------------------------------------
        # MAIN MERCHANT ACCOUNT
        # ---------------------------------------------------------------------
        for row in rows:
            if row.account != main_merchant_account:
                continue

            bucket = movements[
                (posting_date, main_merchant_account)
            ]

            update_bucket_metadata(
                bucket=bucket,
                posting_date=posting_date,
                account=main_merchant_account,
                voucher_type=voucher_type,
                voucher_no=voucher_no,
                transaction_user=transaction_user,
                voucher_mode=voucher_mode,
                account_modes=mode_of_payment_by_account.get(
                    main_merchant_account
                ),
                remarks=row.remarks,
            )

            debit = flt(row.debit)
            credit = flt(row.credit)

            if has_merchant_to_main:
                if debit > TOLERANCE:
                    bucket["received_from_merchants"] += debit

                    for source in merchant_credits:
                        bucket["received_from"].add(
                            source.account
                        )

                if credit > TOLERANCE:
                    bucket["other_outflows"] += credit

                continue

            if has_main_to_bank:
                if credit > TOLERANCE:
                    bucket["transferred_to_bank"] += credit

                    for destination in bank_debits:
                        bucket["transferred_to"].add(
                            destination.account
                        )

                if debit > TOLERANCE:
                    bucket["other_inflows"] += debit

                continue

            if has_main_to_merchant:
                if credit > TOLERANCE:
                    bucket["merchant_transfer_out"] += credit

                    for destination in merchant_debits:
                        bucket["transferred_to"].add(
                            destination.account
                        )

                if debit > TOLERANCE:
                    bucket["other_inflows"] += debit

                continue

            if debit > TOLERANCE:
                bucket["other_inflows"] += debit

            if credit > TOLERANCE:
                bucket["other_outflows"] += credit

        # ---------------------------------------------------------------------
        # BANK ACCOUNTS
        # ---------------------------------------------------------------------
        for row in rows:
            if row.account not in bank_accounts:
                continue

            bucket = movements[(posting_date, row.account)]

            update_bucket_metadata(
                bucket=bucket,
                posting_date=posting_date,
                account=row.account,
                voucher_type=voucher_type,
                voucher_no=voucher_no,
                transaction_user=transaction_user,
                voucher_mode=voucher_mode,
                account_modes=mode_of_payment_by_account.get(
                    row.account
                ),
                remarks=row.remarks,
            )

            debit = flt(row.debit)
            credit = flt(row.credit)

            if has_main_to_bank:
                if debit > TOLERANCE:
                    bucket["received_from_main"] += debit
                    bucket["received_from"].add(
                        main_merchant_account
                    )

                if credit > TOLERANCE:
                    bucket["other_outflows"] += credit

                continue

            if debit > TOLERANCE:
                bucket["other_inflows"] += debit

            if credit > TOLERANCE:
                bucket["other_outflows"] += credit

    return movements


def group_entries_by_voucher(gl_entries):
    grouped = defaultdict(list)

    for row in gl_entries:
        key = (
            getdate(row.posting_date),
            row.voucher_type,
            row.voucher_no,
        )

        grouped[key].append(row)

    return grouped


def new_movement_bucket():
    return {
        "date": None,
        "account": None,
        "users": set(),
        "modes_of_payment": set(),
        "voucher_numbers": set(),
        "voucher_types": set(),
        "remarks": set(),
        "received_from": set(),
        "transferred_to": set(),

        "collections": 0.0,
        "refunds": 0.0,

        "received_from_merchants": 0.0,
        "received_from_main": 0.0,

        "merchant_transfer_in": 0.0,
        "merchant_transfer_out": 0.0,

        "transferred_to_main": 0.0,
        "transferred_to_bank": 0.0,

        "other_inflows": 0.0,
        "other_outflows": 0.0,
    }


def update_bucket_metadata(
    bucket,
    posting_date,
    account,
    voucher_type,
    voucher_no,
    transaction_user,
    voucher_mode,
    account_modes,
    remarks,
):
    bucket["date"] = posting_date
    bucket["account"] = account

    if transaction_user:
        bucket["users"].add(transaction_user)

    if voucher_mode:
        bucket["modes_of_payment"].add(voucher_mode)

    for mode in account_modes or []:
        if mode:
            bucket["modes_of_payment"].add(mode)

    if voucher_no:
        bucket["voucher_numbers"].add(voucher_no)

    if voucher_type:
        bucket["voucher_types"].add(voucher_type)

    if remarks:
        bucket["remarks"].add(str(remarks).strip())


# =============================================================================
# REPORT ROWS
# =============================================================================


def build_report_rows(
    filters,
    merchant_accounts,
    main_merchant_account,
    bank_accounts,
    account_details,
    opening_balances,
    movements,
):
    ordered_accounts = (
        list(merchant_accounts)
        + [main_merchant_account]
        + list(bank_accounts)
    )

    running_balances = {
        account: flt(opening_balances.get(account))
        for account in ordered_accounts
    }

    data = []
    current_date = getdate(filters.from_date)
    to_date = getdate(filters.to_date)

    while current_date <= to_date:
        for account in ordered_accounts:
            movement = movements.get(
                (current_date, account),
                new_movement_bucket(),
            )

            account_detail = account_details.get(
                account,
                frappe._dict(
                    {
                        "name": account,
                        "account_type": "",
                    }
                ),
            )

            if account == main_merchant_account:
                account_role = "Main Merchant"

            elif account in bank_accounts:
                account_role = "Bank Account"

            else:
                account_role = "POS Merchant"

            row = make_report_row(
                posting_date=current_date,
                account=account,
                account_detail=account_detail,
                account_role=account_role,
                opening_balance=running_balances.get(
                    account,
                    0.0,
                ),
                movement=movement,
            )

            running_balances[account] = row.closing_balance

            if cint(filters.get("show_zero_activity")):
                data.append(row)

            elif row.has_activity:
                data.append(row)

        current_date = add_days(current_date, 1)

    return data


def make_report_row(
    posting_date,
    account,
    account_detail,
    account_role,
    opening_balance,
    movement,
):
    collections = flt(movement.get("collections"))
    refunds = flt(movement.get("refunds"))
    net_collections = collections - refunds

    received_from_merchants = flt(
        movement.get("received_from_merchants")
    )

    received_from_main = flt(
        movement.get("received_from_main")
    )

    merchant_transfer_in = flt(
        movement.get("merchant_transfer_in")
    )

    merchant_transfer_out = flt(
        movement.get("merchant_transfer_out")
    )

    transferred_to_main = flt(
        movement.get("transferred_to_main")
    )

    transferred_to_bank = flt(
        movement.get("transferred_to_bank")
    )

    other_inflows = flt(
        movement.get("other_inflows")
    )

    other_outflows = flt(
        movement.get("other_outflows")
    )

    total_inflows = (
        net_collections
        + received_from_merchants
        + received_from_main
        + merchant_transfer_in
        + other_inflows
    )

    total_outflows = (
        transferred_to_main
        + merchant_transfer_out
        + transferred_to_bank
        + other_outflows
    )

    available_balance = (
        flt(opening_balance)
        + total_inflows
    )

    closing_balance = (
        available_balance
        - total_outflows
    )

    if account_role == "POS Merchant":
        expected_transfer = max(net_collections, 0.0)
        actual_transfer = transferred_to_main

    elif account_role == "Main Merchant":
        # This is the key corrected rule:
        # Expected bank transfer equals today's amount received
        # from merchants, not all Cash account transfers.
        expected_transfer = received_from_merchants
        actual_transfer = transferred_to_bank

    else:
        expected_transfer = received_from_main
        actual_transfer = received_from_main

    transfer_variance = (
        actual_transfer - expected_transfer
    )

    pending_transfer = max(
        expected_transfer - actual_transfer,
        0.0,
    )

    excess_transfer = max(
        actual_transfer - expected_transfer,
        0.0,
    )

    has_activity = any(
        abs(flt(value)) > TOLERANCE
        for value in (
            collections,
            refunds,
            received_from_merchants,
            received_from_main,
            merchant_transfer_in,
            merchant_transfer_out,
            transferred_to_main,
            transferred_to_bank,
            other_inflows,
            other_outflows,
        )
    )

    status = determine_status(
        account_role=account_role,
        expected_transfer=expected_transfer,
        actual_transfer=actual_transfer,
        has_activity=has_activity,
    )

    voucher_numbers = sorted(
        movement.get("voucher_numbers") or []
    )

    voucher_types = sorted(
        movement.get("voucher_types") or []
    )

    voucher_no = (
        voucher_numbers[0]
        if len(voucher_numbers) == 1
        else ""
    )

    voucher_type = (
        voucher_types[0]
        if len(voucher_types) == 1
        else ""
    )

    remarks = " | ".join(
        sorted(movement.get("remarks") or [])[:3]
    )

    if len(voucher_numbers) > 1:
        count_text = _("{0} transactions").format(
            len(voucher_numbers)
        )

        remarks = (
            "{0} | {1}".format(count_text, remarks)
            if remarks
            else count_text
        )

    return frappe._dict(
        {
            "date": posting_date,
            "account_role": account_role,
            "account": account,
            "account_type": account_detail.get(
                "account_type"
            ) or "",

            "user": join_values(
                movement.get("users")
            ),

            "mode_of_payment": join_values(
                movement.get("modes_of_payment")
            ),

            "opening_balance": flt(opening_balance),
            "collections": flt(collections),
            "refunds": flt(refunds),
            "net_collections": flt(net_collections),

            "received_from_merchants": flt(
                received_from_merchants
            ),

            "merchant_transfer_in": flt(
                merchant_transfer_in
            ),

            "other_inflows": flt(other_inflows),
            "available_balance": flt(available_balance),

            "transferred_to_main": flt(
                transferred_to_main
            ),

            "merchant_transfer_out": flt(
                merchant_transfer_out
            ),

            "transferred_to_bank": flt(
                transferred_to_bank
            ),

            "other_outflows": flt(other_outflows),
            "closing_balance": flt(closing_balance),

            "expected_transfer": flt(
                expected_transfer
            ),

            "actual_transfer": flt(
                actual_transfer
            ),

            "pending_transfer": flt(
                pending_transfer
            ),

            "excess_transfer": flt(
                excess_transfer
            ),

            "transfer_variance": flt(
                transfer_variance
            ),

            "received_from": join_values(
                movement.get("received_from")
            ),

            "transferred_to": join_values(
                movement.get("transferred_to")
            ),

            "status": status,
            "transaction_count": cint(
                len(voucher_numbers)
            ),

            "voucher_no": voucher_no,
            "voucher_type": voucher_type,
            "remarks": remarks or "",

            "has_activity": has_activity,
            "row_type": "account",
        }
    )


def determine_status(
    account_role,
    expected_transfer,
    actual_transfer,
    has_activity,
):
    expected_transfer = flt(expected_transfer, 2)
    actual_transfer = flt(actual_transfer, 2)

    if not has_activity:
        return "No Activity"

    if account_role == "Bank Account":
        if actual_transfer > TOLERANCE:
            return "Received by Bank"

        return "Bank Activity"

    difference = actual_transfer - expected_transfer

    if abs(difference) <= TOLERANCE:
        if account_role == "POS Merchant":
            return "Closed"

        if account_role == "Main Merchant":
            return "Settled"

        return "Reconciled"

    if expected_transfer > TOLERANCE and actual_transfer <= TOLERANCE:
        if account_role == "POS Merchant":
            return "Not Closed"

        if account_role == "Main Merchant":
            return "Pending Bank Transfer"

    if actual_transfer < expected_transfer - TOLERANCE:
        if account_role == "POS Merchant":
            return "Partially Closed"

        if account_role == "Main Merchant":
            return "Partially Settled"

    if actual_transfer > expected_transfer + TOLERANCE:
        return "Excess Transfer"

    return "Variance"


# =============================================================================
# FILTERING
# =============================================================================


def apply_report_filters(data, filters):
    account_filter = filters.get("account")
    account_role_filter = filters.get("account_role")
    status_filter = filters.get("status")
    exceptions_only = cint(filters.get("exceptions_only"))

    normal_statuses = {
        "Closed",
        "Settled",
        "Received by Bank",
        "Bank Activity",
        "No Activity",
    }

    result = []

    for row in data:
        if (
            account_filter
            and row.account != account_filter
        ):
            continue

        if (
            account_role_filter
            and row.account_role != account_role_filter
        ):
            continue

        if (
            status_filter
            and row.status != status_filter
        ):
            continue

        if (
            exceptions_only
            and row.status in normal_statuses
        ):
            continue

        result.append(row)

    return result


# =============================================================================
# REPORT SUMMARY
# =============================================================================


def build_report_summary(data):
    merchant_rows = [
        row
        for row in data
        if row.get("account_role") == "POS Merchant"
    ]

    main_rows = [
        row
        for row in data
        if row.get("account_role") == "Main Merchant"
    ]

    bank_rows = [
        row
        for row in data
        if row.get("account_role") == "Bank Account"
    ]

    total_net_collections = sum(
        flt(row.get("net_collections"))
        for row in merchant_rows
    )

    total_transferred_to_main = sum(
        flt(row.get("transferred_to_main"))
        for row in merchant_rows
    )

    merchant_pending = sum(
        flt(row.get("pending_transfer"))
        for row in merchant_rows
    )

    received_by_main = sum(
        flt(row.get("received_from_merchants"))
        for row in main_rows
    )

    transferred_to_bank = sum(
        flt(row.get("transferred_to_bank"))
        for row in main_rows
    )

    pending_bank_transfer = sum(
        flt(row.get("pending_transfer"))
        for row in main_rows
    )

    excess_bank_transfer = sum(
        flt(row.get("excess_transfer"))
        for row in main_rows
    )

    received_by_banks = sum(
        flt(row.get("received_from_main"))
        for row in bank_rows
    )

    exception_count = sum(
        1
        for row in data
        if row.get("status")
        in (
            "Not Closed",
            "Partially Closed",
            "Pending Bank Transfer",
            "Partially Settled",
            "Excess Transfer",
            "Variance",
        )
    )

    return [
        {
            "value": total_net_collections,
            "indicator": "Blue",
            "label": _("Net POS Collections"),
            "datatype": "Currency",
        },
        {
            "value": total_transferred_to_main,
            "indicator": (
                "Green"
                if merchant_pending <= TOLERANCE
                else "Orange"
            ),
            "label": _("POS to Main Merchant"),
            "datatype": "Currency",
        },
        {
            "value": merchant_pending,
            "indicator": (
                "Green"
                if merchant_pending <= TOLERANCE
                else "Red"
            ),
            "label": _("Pending POS Closing"),
            "datatype": "Currency",
        },
        {
            "value": received_by_main,
            "indicator": "Blue",
            "label": _("Received by Main Merchant"),
            "datatype": "Currency",
        },
        {
            "value": transferred_to_bank,
            "indicator": (
                "Green"
                if pending_bank_transfer <= TOLERANCE
                else "Orange"
            ),
            "label": _("Main Merchant to Banks"),
            "datatype": "Currency",
        },
        {
            "value": pending_bank_transfer,
            "indicator": (
                "Green"
                if pending_bank_transfer <= TOLERANCE
                else "Red"
            ),
            "label": _("Pending Bank Transfer"),
            "datatype": "Currency",
        },
        {
            "value": excess_bank_transfer,
            "indicator": (
                "Green"
                if excess_bank_transfer <= TOLERANCE
                else "Orange"
            ),
            "label": _("Excess from Prior Balance"),
            "datatype": "Currency",
        },
        {
            "value": received_by_banks,
            "indicator": "Green",
            "label": _("Received by Bank Accounts"),
            "datatype": "Currency",
        },
        {
            "value": exception_count,
            "indicator": (
                "Green"
                if exception_count == 0
                else "Red"
            ),
            "label": _("Exceptions"),
            "datatype": "Int",
        },
    ]


# =============================================================================
# CHART
# =============================================================================


def build_chart(data):
    daily = defaultdict(
        lambda: {
            "collections": 0.0,
            "merchant_to_main": 0.0,
            "main_received": 0.0,
            "main_to_bank": 0.0,
        }
    )

    for row in data:
        date_key = str(row.get("date"))

        if row.get("account_role") == "POS Merchant":
            daily[date_key]["collections"] += flt(
                row.get("net_collections")
            )

            daily[date_key]["merchant_to_main"] += flt(
                row.get("transferred_to_main")
            )

        elif row.get("account_role") == "Main Merchant":
            daily[date_key]["main_received"] += flt(
                row.get("received_from_merchants")
            )

            daily[date_key]["main_to_bank"] += flt(
                row.get("transferred_to_bank")
            )

    labels = sorted(daily.keys())

    if not labels:
        return None

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Net POS Collections"),
                    "values": [
                        daily[date]["collections"]
                        for date in labels
                    ],
                },
                {
                    "name": _("POS to Main"),
                    "values": [
                        daily[date]["merchant_to_main"]
                        for date in labels
                    ],
                },
                {
                    "name": _("Main Received"),
                    "values": [
                        daily[date]["main_received"]
                        for date in labels
                    ],
                },
                {
                    "name": _("Main to Bank"),
                    "values": [
                        daily[date]["main_to_bank"]
                        for date in labels
                    ],
                },
            ],
        },
        "type": "bar",
        "height": 300,
    }


# =============================================================================
# HELPERS
# =============================================================================


def unique_list(values):
    result = []
    seen = set()

    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)

    return result


def join_values(values):
    return ", ".join(
        sorted(
            str(value)
            for value in (values or [])
            if value
        )
    )


def first_value(rows, fieldname):
    for row in rows:
        value = row.get(fieldname)

        if value:
            return value

    return None