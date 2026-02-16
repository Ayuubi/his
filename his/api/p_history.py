import frappe
from frappe.utils import getdate, sanitize_html
from datetime import datetime # from python std library
from frappe.utils import add_to_date
years = add_to_date(getdate(), years=-1) 



@frappe.whitelist()
def get_history(patient , from_date = "2019-01-01", to_date = getdate()):
    history_config = frappe.get_doc("Patient History Configuration" , "Patient History Configuration")
    p_history = []
    conditions  = ''
  
    for config in history_config.history_document:
        table_header  = []
        if config.condition:
            conditions = f"and {config.condition}"
        join = ''
        fields = ''
        join_fields = ''
        if config.parent_document_fields:
            p_fields = config.parent_document_fields.split(",")
            for f in p_fields:
                fields += "p." + f +','
                he = f.replace("_" , " ").title()
                table_header.append(he)
       

        if config.child_document_fields:
            p_fields = config.child_document_fields.split(",")
            for f in p_fields:
                join_fields += "c." + f +','
                he = f.replace("_" , " ").title()
                table_header.append(he)
        join_fields = join_fields[:-1]
        if not join_fields:
             fields = fields[:-1]
        if config.child_document:
            join = f'left join `tab{config.child_document}`  c on p.name =  c.parent' 

        data = frappe.db.sql(f"""
            select {fields}  {join_fields}
            from `tab{config.parent_document}`p
            {join}
            where patient  = '{patient}' and  p.docstatus !=1

        
         """ , as_dict = 1)
        p_history.append({"data" : data , "header" : table_header , "heading" : config.heading})
    frappe.errprint(p_history)
    report_html_data = frappe.render_template(
	"his/templates/report/all_p_history.html",
        {

        "patient" : patient,
        "table": p_history,
        "letter_head": frappe.db.get_value("Letter Head",{"is_default": 1}, "image")

        }
	)
	# html = frappe.render_template(
	# 	base_template_path,
	# 	{"body": report_html_data ,"css" : get_print_style() , "title": "Statement For "},
	# )
    
    return report_html_data


try:
    # v14 should have this
    from frappe.utils import sanitize_html
except Exception:
    sanitize_html = None


_HTML_FIELD_TYPES = {"Text Editor", "HTML", "Markdown Editor"}


def _split(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _num(x):
    try:
        return float(str(x).strip())
    except Exception:
        return None


def _parse_range(rng):
    # accepts "12-16 g/dl" or "0-125" etc.
    if not rng:
        return (None, None)
    s = str(rng).replace("–", "-")
    parts = s.split()
    a = parts[0] if parts else ""
    if "-" not in a:
        return (None, None)
    lo, hi = a.split("-", 1)
    return (_num(lo), _num(hi))


def _flag(result, normal_range):
    r = _num(result)
    lo, hi = _parse_range(normal_range)
    if r is None or lo is None or hi is None:
        return ""
    if r < lo:
        return "↓"
    if r > hi:
        return "↑"
    return ""


def _docstatus_condition(c):
    """
    require_submitted checkbox:
    - if checked: only submitted (1)
    - else: draft or submitted (0/1)
    """
    if getattr(c, "require_submitted", 0):
        return " AND p.docstatus = 1 "
    return " AND p.docstatus IN (0, 1) "


def _is_empty(v):
    return v in (None, "", 0)


def _sanitize(v):
    # best-effort sanitize (prevents unsafe HTML)
    if sanitize_html:
        try:
            return sanitize_html(v)
        except Exception:
            return v
    return v


def _field_meta(doctype, fieldname):
    """Return DocField meta (df) if field exists in doctype."""
    if not doctype or not fieldname:
        return None
    try:
        meta = frappe.get_meta(doctype)
        return meta.get_field(fieldname)
    except Exception:
        return None


def _field_label(doctype, fieldname):
    """
    Prefer DocField.label from Meta.
    Fallback to labelized fieldname if not found.
    """
    df = _field_meta(doctype, fieldname)
    if df and df.label:
        return df.label
    return str(fieldname or "").replace("_", " ").strip().title()


def _is_html_field(doctype, fieldname):
    df = _field_meta(doctype, fieldname)
    return bool(df and df.fieldtype in _HTML_FIELD_TYPES)


def _build_fields_from_config(row, parent_fields, child_fields, parent_dt=None, child_dt=None):
    """
    Build a {label,value,is_html} list from configured parent/child fields.
    ✅ Uses DocField.label (not fieldname) whenever possible.
    ✅ Detects html fields via DocField.fieldtype.
    """
    out = []
    keys = (parent_fields or []) + (child_fields or [])
    seen = set()

    for k in keys:
        k = (k or "").strip()
        if not k or k in seen:
            continue
        seen.add(k)

        v = row.get(k)
        if _is_empty(v):
            continue

        # decide whether this key belongs to parent or child (parent wins if both exist)
        use_dt = None
        if parent_dt and _field_meta(parent_dt, k):
            use_dt = parent_dt
        elif child_dt and _field_meta(child_dt, k):
            use_dt = child_dt

        label = _field_label(use_dt, k) if use_dt else str(k).replace("_", " ").strip().title()
        is_html = _is_html_field(use_dt, k) if use_dt else False

        val = str(v)
        if is_html:
            val = _sanitize(val)

        out.append({"label": label, "value": val, "is_html": is_html})

    return out


def _merge_fields(existing, new_fields):
    """
    When JOIN returns multiple rows per parent, merge instead of overwrite.
    Keep first non-empty label.
    """
    existing = existing or []
    if not new_fields:
        return existing

    seen = {f.get("label") for f in existing if f.get("label")}
    for f in new_fields:
        lbl = f.get("label")
        if not lbl or lbl in seen:
            continue
        if _is_empty(f.get("value")):
            continue
        existing.append(f)
        seen.add(lbl)
    return existing


def _merge_raw(existing_raw, row):
    """
    Keep a raw dict (JS can use it for fallback).
    Do not overwrite existing non-empty values.
    """
    existing_raw = existing_raw or {}
    if not row:
        return existing_raw

    for k, v in row.items():
        if _is_empty(v):
            continue
        if k not in existing_raw:
            existing_raw[k] = v
    return existing_raw


def _pick_date(row):
    for k in ("date", "encounter_date", "start_date", "signs_date", "creation", "modified"):
        if row.get(k):
            return str(row.get(k))
    return ""


def _pick_doctor(row):
    return str(
        row.get("practitioner_name")
        or row.get("practitioner")
        or row.get("full_name")
        or ""
    )


def _merge_section_by_heading(section_map, heading, doctype, cards):
    """
    Merge duplicate headings into ONE section (fixes duplicated History Taken tab).
    Deduplicate cards by a stable id if present (raw.name/title fallback).
    """
    if not cards:
        return

    s = section_map.setdefault(heading, {"heading": heading, "doctype": doctype, "cards": []})

    existing = s["cards"]
    existing_ids = set()

    for c in existing:
        cid = (c.get("id") or (c.get("raw") or {}).get("name") or c.get("title") or "")
        if cid:
            existing_ids.add(cid)

    for c in cards:
        cid = (c.get("id") or (c.get("raw") or {}).get("name") or c.get("title") or "")
        if cid and cid in existing_ids:
            continue
        existing.append(c)
        if cid:
            existing_ids.add(cid)


@frappe.whitelist()
def get_history_view(patient, from_date="2019-01-01", to_date=None):
    to_date = to_date or getdate()

    cfg = frappe.get_doc("Patient History Configuration", "Patient History Configuration")

    # use map so duplicate headings merge into one tab
    section_map = {}

    for c in cfg.history_document:
        # allow hiding sections from config
        if getattr(c, "hidden", 0):
            continue

        heading = (c.heading or "").strip()
        if not heading:
            continue
        heading_l = heading.lower()

        parent_dt = (c.parent_document or "").strip()
        child_dt = (c.child_document or "").strip()

        if not parent_dt:
            continue

        datefield = (c.datefield or "").strip() or "p.creation"
        if "." not in datefield:
            datefield = f"p.{datefield}"

        parent_fields = _split(c.parent_document_fields)
        child_fields = _split(c.child_document_fields)

        # Always include p.name for stable grouping + dedupe
        select_parts = ["p.name AS docname"]

        # ✅ LAB: force include template/date so titles become CBC/Urine correctly even if config misses them
        if parent_dt.lower() == "lab result":
            select_parts += [
                "p.template AS template",
                "p.date AS date",
            ]

        # add configured parent fields
        for f in parent_fields:
            f = (f or "").strip()
            if not f or f.lower() in ("name", "docname"):
                continue
            select_parts.append(f"p.`{f}` AS `{f}`")

        join_sql = ""
        if child_dt:
            join_sql = f" LEFT JOIN `tab{child_dt}` ch ON ch.parent = p.name "
            for f in child_fields:
                f = (f or "").strip()
                if not f:
                    continue
                select_parts.append(f"ch.`{f}` AS `{f}`")

        extra_condition_sql = f" AND ({c.condition}) " if c.condition else ""
        docstatus_sql = _docstatus_condition(c)

        rows = frappe.db.sql(
            f"""
            SELECT {", ".join(select_parts)}
            FROM `tab{parent_dt}` p
            {join_sql}
            WHERE p.patient = %(patient)s
              {docstatus_sql}
              AND {datefield} BETWEEN %(from_date)s AND %(to_date)s
              {extra_condition_sql}
            ORDER BY {datefield} DESC
            LIMIT 1000
            """,
            {"patient": patient, "from_date": from_date, "to_date": to_date},
            as_dict=True,
        )

        # no rows => no tab
        if not rows:
            continue

        cards = []

        # -------------------------
        # MEDICATION
        # -------------------------
        if "prescription" in heading_l or "medication" in heading_l or "drug" in heading_l:
            grouped = {}
            for r in rows:
                enc_date = str(r.get("encounter_date") or r.get("date") or "")
                doctor = _pick_doctor(r)
                key = f"{enc_date}::{doctor}"

                g = grouped.setdefault(
                    key,
                    {
                        "type": "medication",
                        "title": f"{heading} — {enc_date}",
                        "sub": doctor,
                        "lines": [],
                        "raw": {},
                        "id": key,
                    },
                )

                drug = r.get("drug_code") or r.get("drug") or r.get("item")
                qty = r.get("qty")
                dosage = r.get("dosage")

                if drug:
                    g["lines"].append(
                        {"drug": str(drug), "qty": str(qty or ""), "dosage": str(dosage or "")}
                    )

                g["raw"] = _merge_raw(g.get("raw"), r)

            cards = [g for g in grouped.values() if g.get("lines")]

        # -------------------------
        # LAB RESULT
        # -------------------------
        elif "lab result" in heading_l or parent_dt.lower() == "lab result":
            grouped = {}
            for r in rows:
                template = str(r.get("template") or "Lab")
                dt = str(r.get("date") or _pick_date(r))
                doc = _pick_doctor(r)

                # ✅ group by Lab Result document name (best)
                docname = r.get("docname") or ""
                key = docname or f"{template}::{dt}::{doc}"

                g = grouped.setdefault(
                    key,
                    {
                        "type": "lab",
                        "title": f"{template} — {dt}",
                        "sub": doc,
                        "tests": [],
                        "raw": {},
                        "id": key,
                    },
                )

                # ✅ IMPORTANT: NEVER fall back to docname for test name
                test = (r.get("lab_test_name") or r.get("lab_test_event") or r.get("test"))
                if test:
                    res = r.get("result_value") or r.get("result")
                    rng = r.get("normal_range") or r.get("range")
                    g["tests"].append(
                        {
                            "name": str(test),
                            "result": str(res or ""),
                            "range": str(rng or ""),
                            "uom": str(r.get("lab_test_uom") or r.get("uom") or ""),
                            "flag": _flag(res, rng),
                        }
                    )

                g["raw"] = _merge_raw(g.get("raw"), r)

            cards = [g for g in grouped.values() if g.get("tests")]

        # -------------------------
        # VITALS
        # -------------------------
        elif "vital" in heading_l or parent_dt.lower() in ("vital signs", "vital signs entry", "vital_signs"):
            vit_rows = []
            for r in rows:
                dt = str(r.get("signs_date") or r.get("date") or _pick_date(r))
                vit = {"date": dt}

                for f in parent_fields:
                    if f and f not in ("name", "patient", "docstatus"):
                        if not _is_empty(r.get(f)):
                            vit[f] = r.get(f)

                vit_rows.append(vit)

            cards = (
                [{"type": "vitals", "title": heading, "sub": "", "rows": vit_rows[:200], "id": f"{heading}::vitals"}]
                if vit_rows
                else []
            )

        # -------------------------
        # EVENTS / DEFAULT (dynamic from config)
        # -------------------------
        else:
            grouped = {}
            for r in rows:
                dt = _pick_date(r)
                doc = _pick_doctor(r)

                # stable key: parent doc name
                key = r.get("docname") or f"{dt}::{doc}"

                g = grouped.setdefault(
                    key,
                    {"type": "event", "title": f"{heading} — {dt}", "sub": doc, "fields": [], "raw": {}, "id": key},
                )

                new_fields = _build_fields_from_config(r, parent_fields, child_fields, parent_dt, child_dt)
                g["fields"] = _merge_fields(g.get("fields"), new_fields)
                g["raw"] = _merge_raw(g.get("raw"), r)

            cards = list(grouped.values())

        # if cards ended up empty, do not return section
        if not cards:
            continue

        _merge_section_by_heading(section_map, heading, parent_dt, cards)

    sections = list(section_map.values())

    patient_name = frappe.db.get_value("Patient", patient, "patient_name") or ""

    return {
        "patient": patient,
        "patient_name": patient_name,
        "from_date": from_date,
        "to_date": str(to_date),
        "sections": sections,
    }
