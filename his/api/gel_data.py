import frappe

@frappe.whitelist()
def get_customer_balance_by_cost_center(cost_center, party_type=None, party=None):
    today = frappe.utils.today()

    filters = {
        "cost_center": cost_center,
        "docstatus": 1,
        "posting_date": ["<=", today],
        "party_type": "Customer"
    }

    if party_type:
        filters["party_type"] = party_type

    if party:
        filters["party"] = party

    gl_entries = frappe.get_all("GL Entry",
        fields=["party", "account", "debit", "credit"],
        filters=filters)

    party_balances = {}

    for entry in gl_entries:
        party = entry.party
        account = entry.account
        debit = entry.debit
        credit = entry.credit

        if party not in party_balances:
            party_balances[party] = 0.0

        if account.startswith("Accounts Receivable"):
            party_balances[party] += debit - credit
        elif account.startswith("Sales"):
            party_balances[party] -= debit - credit

    return party_balances
