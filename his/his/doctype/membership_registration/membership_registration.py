# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _has_field(doctype: str, fieldname: str) -> bool:
    """Safe meta check (no assumptions)."""
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _allocate_new_card_number() -> int:
    """
    Safe incremental allocator to prevent card_number collisions
    when multiple users create Membership Registration at the same time.

    We lock tabSingles row for HIS Settings:last_card_number.
    """
    frappe.db.sql(
        """
        SELECT value
        FROM `tabSingles`
        WHERE doctype='HIS Settings' AND field='last_card_number'
        FOR UPDATE
        """
    )

    last_card = frappe.db.get_single_value("HIS Settings", "last_card_number") or 0
    new_card = int(last_card) + 1

    frappe.db.set_value(
        "HIS Settings",
        "HIS Settings",
        "last_card_number",
        new_card,
        update_modified=False
    )
    return new_card


def _get_or_create_membership_customer_group() -> str:
    """
    Uses HIS Settings.default_customer_group if set, else 'Membership'.
    Ensures Customer Group exists, and stores it back in settings.
    """
    group = frappe.db.get_single_value("HIS Settings", "default_customer_group") or "Membership"

    if not frappe.db.exists("Customer Group", group):
        frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": group,
            "parent_customer_group": "All Customer Groups",
            "is_group": 0,
        }).insert(ignore_permissions=True)

    # persist selection so admins see it in settings
    frappe.db.set_value(
        "HIS Settings",
        "HIS Settings",
        "default_customer_group",
        group,
        update_modified=False
    )
    return group


def _effective_status(doc) -> str:
    """
    Returns: 'Active' / 'Inactive' / 'Expired'
    Rules:
      - If doc.status != 'Active' => Inactive
      - If status 'Active' but end_date passed => Expired
      - Else Active
    """
    if (doc.status or "") != "Active":
        return "Inactive"

    if doc.end_date:
        if getdate(nowdate()) > getdate(doc.end_date):
            return "Expired"

    return "Active"


def _set_membership_customer_group_for_patient(patient_doc, membership_group: str):
    """
    Option 1 policy:
      - Set customer group ONLY when membership is Active.
      - Do NOT revert customer group when membership becomes Inactive/Expired.

    Implementation (no assumptions):
      1) If Patient has custom field 'customer_group' -> set it
      2) Else if Patient has link field 'customer' and it has value -> set Customer.customer_group
      3) Else skip
    """
    if _has_field("Patient", "customer_group"):
        patient_doc.customer_group = membership_group
        return

    if _has_field("Patient", "customer"):
        cust = getattr(patient_doc, "customer", None)
        if cust and frappe.db.exists("Customer", cust):
            frappe.db.set_value("Customer", cust, "customer_group", membership_group, update_modified=False)


def _apply_person_fields_to_patient(patient_doc, *, full_name=None, mobile=None, sex=None, age=None, age_type=None, district=None):
    """
    Updates patient demographic fields (only if values provided).
    Uses safe field checks for district mappings.
    """
    if full_name:
        patient_doc.first_name = full_name

    if mobile:
        patient_doc.mobile_no = mobile

    if sex:
        # Patient has 'sex' in ERPNext Healthcare; keep as-is
        patient_doc.sex = sex

    # IMPORTANT: p_age may be required by your custom patient hook; set only if provided
    if age is not None and age != "":
        patient_doc.p_age = age

    if age_type:
        patient_doc.age_type = age_type

    # District mapping (no assumptions)
    if district:
        if _has_field("Patient", "district"):
            patient_doc.district = district
        elif _has_field("Patient", "territory"):
            patient_doc.territory = district
        # else: skip silently


def _apply_membership_fields_to_patient(patient_doc, doc, membership_group: str | None = None):
    """
    Sets ONLY membership-owned fields on Patient.
    Option 1: does NOT revert customer group on inactive/expired.
    """
    eff = _effective_status(doc)

    if eff == "Active":
        patient_doc.percentage = doc.discount_level or 0
        patient_doc.is_membership = "Membership"
    else:
        patient_doc.percentage = 0
        patient_doc.is_membership = ""

    # Linkage fields (these are your custom patient fields you already use)
    patient_doc.membership = doc.name
    patient_doc.member_card = doc.card_number
    patient_doc.member_company = doc.company
    patient_doc.member_contact = doc.contact_number
    patient_doc.member_head = doc.family_head_person
    patient_doc.member_card_status = eff

    # Customer group set ONLY when Active
    if membership_group and eff == "Active":
        _set_membership_customer_group_for_patient(patient_doc, membership_group)


def _sync_patient(patient_name: str, doc, membership_group: str | None = None):
    """Apply membership fields to an existing Patient safely."""
    if not patient_name:
        return
    if not frappe.db.exists("Patient", patient_name):
        return

    p = frappe.get_doc("Patient", patient_name)
    _apply_membership_fields_to_patient(p, doc, membership_group)
    p.save(ignore_permissions=True)


# ---------------------------------------------------------
# DocType Controller
# ---------------------------------------------------------

class MembershipRegistration(Document):
    def validate(self):
        """
        - Compute total rows
        - Default dates
        - Validate end_date >= start_date
        """
        self.total = len(self.family_members or [])

        # Your exact fieldname: registeration_date
        if not self.registeration_date:
            self.registeration_date = nowdate()

        if not self.start_date:
            self.start_date = self.registeration_date

        if self.start_date and self.end_date:
            if getdate(self.end_date) < getdate(self.start_date):
                frappe.throw("End Date cannot be before Start Date.")

    def before_insert(self):
        """Allocate card_number once for new documents."""
        if not self.card_number:
            self.card_number = _allocate_new_card_number()

    def on_submit(self):
        """
        Head patient create/update deterministically using:
          - Parent field: head_patient (Link Patient)

        Rule:
          - If head_patient exists => UPDATE that Patient
          - Else => CREATE a new Patient and set head_patient
        """
        membership_group = _get_or_create_membership_customer_group()

        # Collect head fields from parent.
        # NOTE: You added these to your parent (as per your latest paste):
        head_sex = getattr(self, "sex", None)
        head_age = getattr(self, "age", None)
        head_age_type = getattr(self, "age_type", None)
        head_district = getattr(self, "district", None)

        if self.head_patient:
            # UPDATE existing head patient
            p = frappe.get_doc("Patient", self.head_patient)

            _apply_person_fields_to_patient(
                p,
                full_name=self.family_head_person,
                mobile=self.contact_number,
                sex=head_sex,
                age=head_age,
                age_type=head_age_type,
                district=head_district,
            )

            _apply_membership_fields_to_patient(p, self, membership_group)
            p.save(ignore_permissions=True)

        else:
            # CREATE new head patient
            if not self.family_head_person:
                frappe.throw("Family Head Person is required to create a new head patient.")
            if not self.contact_number:
                frappe.throw("Contact Number is required to create a new head patient.")

            p = frappe.get_doc({"doctype": "Patient"})

            _apply_person_fields_to_patient(
                p,
                full_name=self.family_head_person,
                mobile=self.contact_number,
                sex=head_sex,
                age=head_age,
                age_type=head_age_type,
                district=head_district,
            )

            _apply_membership_fields_to_patient(p, self, membership_group)
            p.insert(ignore_permissions=True)

            self.head_patient = p.name
            self.db_set("head_patient", p.name, update_modified=False)

    def on_update(self):
        """
        Keep linked patients in sync whenever anything changes:
          - status / discount_level / start_date / end_date
        """
        membership_group = _get_or_create_membership_customer_group()

        # Sync head
        if self.head_patient:
            _sync_patient(self.head_patient, self, membership_group)

        # Sync registered family members
        for row in (self.family_members or []):
            if row.patient:
                _sync_patient(row.patient, self, membership_group)


# ---------------------------------------------------------
# Register / Update APIs
# ---------------------------------------------------------

@frappe.whitelist()
def register_family_members(docname):
    """
    Process all rows that are not visited.
    Deterministic rule:
      - if row.patient exists => UPDATE that patient
      - else => CREATE new patient from row fields
    """
    doc = frappe.get_doc("Membership Registration", docname)
    membership_group = _get_or_create_membership_customer_group()

    registered = []
    skipped = []

    for row in (doc.family_members or []):
        if row.visited:
            continue

        # CREATE mode requires minimum fields
        if not row.patient:
            if not row.full_name or not row.mobile or not row.age:
                skipped.append({
                    "row": row.idx,
                    "name": row.full_name,
                    "reason": "Missing Full Name / Mobile / Age for new patient"
                })
                continue

        try:
            if row.patient:
                # UPDATE mode
                p = frappe.get_doc("Patient", row.patient)

                _apply_person_fields_to_patient(
                    p,
                    full_name=row.full_name,
                    mobile=row.mobile,
                    sex=row.sex,
                    age=row.age,
                    age_type=row.age_type,
                    district=getattr(row, "dr", None),  # your child field is dr (Territory link)
                )

                _apply_membership_fields_to_patient(p, doc, membership_group)
                p.save(ignore_permissions=True)

            else:
                # CREATE mode
                p = frappe.get_doc({"doctype": "Patient"})

                _apply_person_fields_to_patient(
                    p,
                    full_name=row.full_name,
                    mobile=row.mobile,
                    sex=row.sex,
                    age=row.age,
                    age_type=row.age_type,
                    district=getattr(row, "dr", None),
                )

                _apply_membership_fields_to_patient(p, doc, membership_group)
                p.insert(ignore_permissions=True)

                row.patient = p.name

            row.visited = 1
            registered.append(row.full_name)

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Membership: Register All")
            skipped.append({
                "row": row.idx,
                "name": row.full_name,
                "reason": "Server error (check error log)"
            })

    doc.save()

    return {
        "registered": registered,
        "skipped": skipped,
        "total_registered": len(registered),
        "total_skipped": len(skipped),
    }


@frappe.whitelist()
def register_single_member(docname, membername):
    """
    Register/Update one row via button.
    membername is the child row.name
    """
    doc = frappe.get_doc("Membership Registration", docname)
    membership_group = _get_or_create_membership_customer_group()

    row = next((r for r in (doc.family_members or []) if r.name == membername), None)
    if not row:
        frappe.throw("Member row not found")

    if row.visited:
        return {"status": "already_registered", "name": row.full_name}

    # CREATE mode requires fields
    if not row.patient:
        if not row.full_name or not row.mobile or not row.age:
            frappe.throw("Full Name, Mobile, Age are required to create a new patient")

    try:
        if row.patient:
            # UPDATE
            p = frappe.get_doc("Patient", row.patient)

            _apply_person_fields_to_patient(
                p,
                full_name=row.full_name,
                mobile=row.mobile,
                sex=row.sex,
                age=row.age,
                age_type=row.age_type,
                district=getattr(row, "dr", None),
            )

            _apply_membership_fields_to_patient(p, doc, membership_group)
            p.save(ignore_permissions=True)

        else:
            # CREATE
            p = frappe.get_doc({"doctype": "Patient"})

            _apply_person_fields_to_patient(
                p,
                full_name=row.full_name,
                mobile=row.mobile,
                sex=row.sex,
                age=row.age,
                age_type=row.age_type,
                district=getattr(row, "dr", None),
            )

            _apply_membership_fields_to_patient(p, doc, membership_group)
            p.insert(ignore_permissions=True)

            row.patient = p.name

        row.visited = 1
        doc.save()

        return {"status": "ok", "name": row.full_name, "patient": row.patient}

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Membership: Register Single")
        frappe.throw("Something went wrong while registering/updating this member")



# # Copyright (c) 2025, Rasiin Tech and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from frappe.utils import nowdate, getdate


# # ---------------------------------------------------------
# # Helpers (Safe card allocator + membership logic)
# # ---------------------------------------------------------

# def _allocate_new_card_number() -> int:
#     # lock the single value row so two requests can't allocate same number
#     frappe.db.sql(
#         """
#         SELECT value
#         FROM `tabSingles`
#         WHERE doctype='HIS Settings' AND field='last_card_number'
#         FOR UPDATE
#         """
#     )

#     last_card = frappe.db.get_single_value("HIS Settings", "last_card_number") or 0
#     new_card = int(last_card) + 1

#     frappe.db.set_value(
#         "HIS Settings",
#         "HIS Settings",
#         "last_card_number",
#         new_card,
#         update_modified=False
#     )
#     return new_card



# def _effective_status(doc) -> str:
#     """
#     Returns: 'Active' / 'Inactive' / 'Expired'
#     - If doc.status != Active => Inactive (manual control wins)
#     - If doc.status == Active and end_date passed => Expired
#     - Else Active
#     """
#     if (doc.status or "") != "Active":
#         return "Inactive"

#     if doc.end_date:
#         if getdate(nowdate()) > getdate(doc.end_date):
#             return "Expired"

#     return "Active"


# def _apply_membership_fields_to_patient(patient_doc, doc):
#     """
#     Sets ONLY membership-owned fields on Patient.
#     (Avoid overwriting other Patient data unintentionally.)
#     """
#     eff = _effective_status(doc)

#     if eff == "Active":
#         patient_doc.percentage = doc.discount_level or 0
#         patient_doc.is_membership = "Membership"
#     else:
#         patient_doc.percentage = 0
#         patient_doc.is_membership = ""

#     # Linkage fields (these are your custom patient fields you already use)
#     patient_doc.membership = doc.name
#     patient_doc.member_card = doc.card_number
#     patient_doc.member_company = doc.company
#     patient_doc.member_contact = doc.contact_number
#     patient_doc.member_head = doc.family_head_person
#     patient_doc.member_card_status = eff


# def _sync_patient(patient_name: str, doc):
#     """Apply membership fields to existing Patient safely."""
#     if not patient_name:
#         return
#     if not frappe.db.exists("Patient", patient_name):
#         return

#     p = frappe.get_doc("Patient", patient_name)
#     _apply_membership_fields_to_patient(p, doc)
#     p.save(ignore_permissions=True)


# # ---------------------------------------------------------
# # DocType Controller
# # ---------------------------------------------------------

# class MembershipRegistration(Document):
#     def validate(self):
#         """
#         - Compute total rows
#         - Default dates
#         - Validate end_date >= start_date
#         """
#         self.total = len(self.family_members or [])

#         # Default registeration_date (your exact fieldname)
#         if not self.registeration_date:
#             self.registeration_date = nowdate()

#         # If start_date empty, default to registeration_date
#         if not self.start_date:
#             self.start_date = self.registeration_date

#         # Validate date range if end_date set
#         if self.start_date and self.end_date:
#             if getdate(self.end_date) < getdate(self.start_date):
#                 frappe.throw("End Date cannot be before Start Date.")

#     def before_insert(self):
#         """
#         Allocate card_number once for new documents.
#         """
#         if not self.card_number:
#             self.card_number = _allocate_new_card_number()

#     def on_submit(self):
#         """
#         HEAD patient create/update deterministically using your fieldname: head_patient
#         - If head_patient exists => Update that patient
#         - If head_patient empty => Create new patient & set head_patient
#         """
#         eff = _effective_status(self)  # computed but not stored; used for patient fields

#         if self.head_patient:
#             # UPDATE existing head patient
#             p = frappe.get_doc("Patient", self.head_patient)

#             # Optional overwrite: only identity fields from membership form
#             if self.family_head_person:
#                 p.first_name = self.family_head_person
#             if self.contact_number:
#                 p.mobile_no = self.contact_number

#             _apply_membership_fields_to_patient(p, self)
#             p.save(ignore_permissions=True)

#         else:
#             # CREATE new head patient
#             if not self.family_head_person:
#                 frappe.throw("Family Head Person is required to create a new head patient.")
#             if not self.contact_number:
#                 frappe.throw("Contact Number is required to create a new head patient.")

#             p = frappe.get_doc({
#                 "doctype": "Patient",
#                 "first_name": self.family_head_person,
#                 "mobile_no": self.contact_number,
#                 "p_age": self.age,          # <-- prevents None crash
#                 "age_type": self.age_type,  # <-- if your Patient requires it
#                 "district": self.district,
#                 "sex": self.sex,
#             })
#             _apply_membership_fields_to_patient(p, self)
#             p.insert(ignore_permissions=True)

#             # store back link
#             self.head_patient = p.name
#             self.db_set("head_patient", p.name, update_modified=False)

#     def on_update(self):
#         """
#         Keep linked patients in sync when:
#         - status changes (Active/Inactive)
#         - discount_level changes
#         - end_date changes (expiry)
#         """
#         # Sync head
#         if self.head_patient:
#             _sync_patient(self.head_patient, self)

#         # Sync all registered family members
#         for row in (self.family_members or []):
#             if row.patient:
#                 _sync_patient(row.patient, self)


# # ---------------------------------------------------------
# # Register / Update APIs
# # ---------------------------------------------------------

# @frappe.whitelist()
# def register_family_members(docname):
#     """
#     Process all rows that are not visited.
#     Deterministic rule:
#       - if row.patient exists => update that patient
#       - else => create a new patient using row fields
#     """
#     doc = frappe.get_doc("Membership Registration", docname)

#     registered = []
#     skipped = []

#     for row in (doc.family_members or []):
#         if row.visited:
#             continue

#         # If CREATE mode (no patient link), require the minimum fields
#         if not row.patient:
#             if not row.full_name or not row.mobile or not row.age:
#                 skipped.append({
#                     "row": row.idx,
#                     "name": row.full_name,
#                     "reason": "Missing Full Name / Mobile / Age for new patient"
#                 })
#                 continue

#         try:
#             if row.patient:
#                 # UPDATE mode
#                 p = frappe.get_doc("Patient", row.patient)

#                 # Controlled overwrites:
#                 if row.full_name:
#                     p.first_name = row.full_name
#                 if row.mobile:
#                     p.mobile_no = row.mobile
#                 if row.sex:
#                     p.sex = row.sex
#                 if row.age:
#                     p.p_age = row.age
#                 if row.age_type:
#                     p.age_type = row.age_type

#                 # If you have a Patient field for district, map it here; otherwise skip.
#                 # Example (ONLY if exists): p.territory = row.dr

#                 _apply_membership_fields_to_patient(p, doc)
#                 p.save(ignore_permissions=True)

#             else:
#                 # CREATE mode
#                 p = frappe.get_doc({
#                     "doctype": "Patient",
#                     "first_name": row.full_name,
#                     "mobile_no": row.mobile,
#                     "sex": row.sex,
#                     "p_age": row.age,
#                     "age_type": row.age_type,
#                 })

#                 _apply_membership_fields_to_patient(p, doc)
#                 p.insert(ignore_permissions=True)

#                 row.patient = p.name

#             row.visited = 1
#             registered.append(row.full_name)

#         except Exception:
#             frappe.log_error(frappe.get_traceback(), "Membership: Register All")
#             skipped.append({
#                 "row": row.idx,
#                 "name": row.full_name,
#                 "reason": "Server error (check error log)"
#             })

#     doc.save()

#     return {
#         "registered": registered,
#         "skipped": skipped,
#         "total_registered": len(registered),
#         "total_skipped": len(skipped),
#     }


# @frappe.whitelist()
# def register_single_member(docname, membername):
#     """
#     Register/Update one row via button.
#     membername is the child row.name
#     """
#     doc = frappe.get_doc("Membership Registration", docname)
#     row = next((r for r in (doc.family_members or []) if r.name == membername), None)

#     if not row:
#         frappe.throw("Member row not found")

#     if row.visited:
#         return {"status": "already_registered", "name": row.full_name}

#     # CREATE mode requires fields
#     if not row.patient:
#         if not row.full_name or not row.mobile or not row.age:
#             frappe.throw("Full Name, Mobile, Age are required to create a new patient")

#     try:
#         if row.patient:
#             # UPDATE
#             p = frappe.get_doc("Patient", row.patient)

#             if row.full_name:
#                 p.first_name = row.full_name
#             if row.mobile:
#                 p.mobile_no = row.mobile
#             if row.sex:
#                 p.sex = row.sex
#             if row.age:
#                 p.p_age = row.age
#             if row.age_type:
#                 p.age_type = row.age_type

#             _apply_membership_fields_to_patient(p, doc)
#             p.save(ignore_permissions=True)

#         else:
#             # CREATE
#             p = frappe.get_doc({
#                 "doctype": "Patient",
#                 "first_name": row.full_name,
#                 "mobile_no": row.mobile,
#                 "sex": row.sex,
#                 "p_age": row.age,
#                 "age_type": row.age_type,
#             })
#             _apply_membership_fields_to_patient(p, doc)
#             p.insert(ignore_permissions=True)

#             row.patient = p.name

#         row.visited = 1
#         doc.save()

#         return {"status": "ok", "name": row.full_name, "patient": row.patient}

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Membership: Register Single")
#         frappe.throw("Something went wrong while registering/updating this member")



# # Copyright (c) 2025, Rasiin Tech and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# class MembershipRegistration(Document):
#     def validate(self):
#         self.total = len(self.family_members)
#         self.flags._previous_status = frappe.db.get_value(self.doctype, self.name, "status")

#     def before_insert(self):
#         # Get last card number from settings
#         last_card = frappe.db.get_single_value("HIS Settings", "last_card_number") or 0
#         new_card = int(last_card) + 1

#         # Assign new card number
#         self.card_number = new_card

#         # Save new last card number
#         frappe.db.set_value("HIS Settings", "HIS Settings", "last_card_number", new_card)

#     def on_update(self):
#         # frappe.errprint(self)
#         # Store initial status on load
#         if self.discount_level and self.status == "Active":
#             # frappe.errprint(f"Inactive IF {previous_status}")
#             for member in self.family_members:
#                 if member.patient:
#                     frappe.db.set_value("Patient", member.patient, {
#                         "percentage": self.discount_level,
                        
#                     })


#         previous_status = getattr(self.flags, "_previous_status", None)
            
#         if self.status == "Inactive" and previous_status != "Inactive":
#             # frappe.errprint(f"Inactive IF {previous_status}")
#             for member in self.family_members:
#                 if member.patient:
#                     try:
#                         frappe.db.set_value("Patient", member.patient, {
#                             "percentage": 0,
#                             # "customer_group": "All Customer Groups",
#                             "is_membership": "",
#                             "member_card_status": "Inactive"
#                         })
#                     except Exception as e:
#                         frappe.log_error(f"Failed to deactivate patient {member.patient}: {str(e)}", "Membership Deactivation")

#         elif self.status == "Active" and previous_status == "Inactive":
#             # frappe.errprint(f"Active ELIF {previous_status}")
#             # customer_group = frappe.db.get_single_value("HIS Settings", "default_customer_group") or "Membership"
#             for member in self.family_members:
#                 if member.patient:
#                     try:
#                         frappe.db.set_value("Patient", member.patient, {
#                             "percentage": self.discount_level,
#                             # "customer_group": customer_group,
#                             "is_membership": "Membership",
#                             "member_card_status": "Active"
#                         })
#                     except Exception as e:
#                         frappe.log_error(f"Failed to reactivate patient {member.patient}: {str(e)}", "Membership Reactivation")




# @frappe.whitelist()
# def register_family_members(docname):
#     doc = frappe.get_doc("Membership Registration", docname)
#     registered = []
#     skipped = []

#     for member in doc.family_members:
#         if member.visited:
#             continue

#         # Validate required fields
#         if not member.full_name or not member.mobile or not member.age:
#             frappe.log_error(f"Incomplete info for member: {member.name}", "Registration Skipped")
#             skipped.append({"name": member.name, "reason": "Incomplete information"})
#             continue

#         try:
#             if member.patient:
#                 updating_patient = frappe.get_doc("Patient", member.patient)
#                 updating_patient.first_name = member.full_name
#                 updating_patient.mobile_no = member.mobile
#                 updating_patient.sex = member.sex
#                 updating_patient.p_age = member.age
#                 updating_patient.age_type = member.age_type
#                 updating_patient.percentage = doc.discount_level
#                 updating_patient.is_membership = "Membership"
#                 # updating_patient.customer_group = customer_group
#                 updating_patient.membership = doc.name
#                 updating_patient.member_card = doc.card_number
#                 updating_patient.member_company = doc.company
#                 updating_patient.member_contact = doc.contact_number
#                 updating_patient.member_head = doc.family_head_person
#                 updating_patient.save()
#                 member.visited = 1
#             else:
#                 patient = frappe.get_doc({
#                     "doctype": "Patient",
#                     "first_name": member.full_name,
#                     "mobile_no": member.mobile,
#                     "sex": member.sex,
#                     "p_age": member.age,
#                     "age_type": member.age_type,
#                     "percentage": doc.discount_level,
#                     "is_membership": "Membership",
#                     # "customer_group": customer_group,
#                     "membership": doc.name,
#                     "member_card": doc.card_number,
#                     "member_company": doc.company,
#                     "member_contact": doc.contact_number,
#                     "member_head": doc.family_head_person
#                 })
#                 patient.insert(ignore_permissions=True)
#                 member.visited = 1
#                 member.patient = patient.name
#             registered.append(member.full_name)
#         except Exception as e:
#             frappe.log_error(f"Error inserting patient for {member.full_name}: {str(e)}", "Membership Error")
#             skipped.append({"name": member.full_name, "reason": str(e)})

#     doc.save()

#     return {
#         "registered": registered,
#         "skipped": skipped,
#         "total_registered": len(registered),
#         "total_skipped": len(skipped)
#     }

# @frappe.whitelist()
# def register_single_member(docname, membername):
#     doc = frappe.get_doc("Membership Registration", docname)
#     member = next((m for m in doc.family_members if m.name == membername), None)

#     if not member:
#         frappe.throw("Member not found")

#     if member.visited:
#         return {"status": "already_registered", "name": member.full_name}

#     # Validate required fields
#     if not member.full_name or not member.mobile or not member.age:
#         frappe.throw(f"Incomplete information for {member.full_name}")

#     try:
#         if member.patient:
#             updating_patient = frappe.get_doc("Patient", member.patient)
#             updating_patient.first_name = member.full_name
#             updating_patient.mobile_no = member.mobile
#             updating_patient.sex = member.sex
#             updating_patient.p_age = member.age
#             updating_patient.age_type = member.age_type
#             updating_patient.percentage = doc.discount_level
#             updating_patient.is_membership = "Membership"
#             # updating_patient.customer_group = customer_group
#             updating_patient.membership = doc.name
#             updating_patient.member_card = doc.card_number
#             updating_patient.member_company = doc.company
#             updating_patient.member_contact = doc.contact_number
#             updating_patient.member_head = doc.family_head_person
#             updating_patient.save()
#             member.visited = 1
#             doc.save()
#             return {"status": "ok", "name": member.full_name}

#         else:
#             patient = frappe.get_doc({
#                 "doctype": "Patient",
#                 "first_name": member.full_name,
#                 "mobile_no": member.mobile,
#                 "sex": member.sex,
#                 "p_age": member.age,
#                 "age_type": member.age_type,
#                 "percentage": doc.discount_level,
#                 "is_membership": "Membership",
#                 # "customer_group": customer_group,
#                 "membership": doc.name,
#                 "member_card": doc.card_number,
#                 "member_company": doc.company,
#                 "member_contact": doc.contact_number,
#                 "member_head": doc.family_head_person
#             })
#             patient.insert(ignore_permissions=True)
#             member.visited = 1
#             member.patient = patient.name
#             doc.save()
#             return {"status": "ok", "name": member.full_name}

#     except Exception as e:
#         frappe.log_error(f"Patient creation failed: {str(e)}", "Register Single")
#         frappe.throw("Something went wrong while registering patient")


