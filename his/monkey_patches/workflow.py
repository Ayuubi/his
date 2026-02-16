# his/monkey_patches/workflow.py

import frappe
from frappe.model import workflow as core_workflow
from his.utils import get_allowed_discount


# keep a reference to the original function
_original_get_workflow_safe_globals = core_workflow.get_workflow_safe_globals


def patched_get_workflow_safe_globals():
    # start from the original globals, so you keep any future Frappe changes
    safe_globals = _original_get_workflow_safe_globals()

    # add your custom function
    safe_globals["get_allowed_discount"] = get_allowed_discount

    return safe_globals


def apply():
    # do the actual monkey patch
    core_workflow.get_workflow_safe_globals = patched_get_workflow_safe_globals


# import frappe
# from frappe.model import workflow
# from his.utils import get_allowed_discount

# old_get_workflow_safe_globals = workflow.get_workflow_safe_globals


# def get_workflow_safe_globals():
#     frappe.msgprint("called called")
#     safe_globals = old_get_workflow_safe_globals()
#     safe_globals["get_allowed_discount"] = get_allowed_discount
#     return safe_globals


# workflow.get_workflow_safe_globals = get_workflow_safe_globals




