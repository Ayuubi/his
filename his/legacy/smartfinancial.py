# his/his/legacy/smartfinancial.py
from __future__ import annotations

import re
import frappe
import pymysql


from frappe.utils import add_days, getdate
from typing import List, Dict, Any
from frappe.utils import cint

# def get_conn():
#     cfg = frappe.local.conf.get("legacy_smartfinancial") or {}
#     missing = [k for k in ("host", "user", "password", "database") if not cfg.get(k)]
#     if missing:
#         frappe.throw(f"Missing legacy_smartfinancial config keys: {', '.join(missing)}")

#     return pymysql.connect(
#         host=cfg["host"],
#         user=cfg["user"],
#         password=cfg["password"],
#         database=cfg["database"],
#         port=int(cfg.get("port", 3306)),
#         charset="utf8mb4",
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True,
#     )

def get_conn():
    cfg = frappe.local.conf.get("legacy_smartfinancial") or {}
    missing = [k for k in ("host", "user", "password", "database") if not cfg.get(k)]
    if missing:
        frappe.throw(f"Missing legacy_smartfinancial config keys: {', '.join(missing)}")

    return pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=int(cfg.get("port", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        init_command="SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
    )


# def fetch_patient_labs(patient_number: str, limit: int = 500):
#     patient_number = (patient_number or "").strip()
#     if not patient_number:
#         return []

#     sql = """
#     SELECT
#     R.DatePerformed,
#     R.ProcedureID,
#     R.ParameterID,
#     R.LabTestResults,
#     R.Reference,
#     H.PatientNumber,
#     H.PatientStatus,
#     D.DoctorName
#     FROM labrequestheader H
#     JOIN labresultdetail R
#     ON H.LabRequestNumber = R.LabRequestNumber
#     JOIN doctorinformation D
#     ON D.DoctorID = H.DoctorID
#     WHERE
#     H.PatientNumber = %s
#     AND R.LabTestResults IS NOT NULL
#     ORDER BY R.DatePerformed DESC
#     LIMIT %s;

#     """

#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute(sql, (patient_number, int(limit)))
#             return cur.fetchall()
#     finally:
#         conn.close()

def fetch_patient_labs(patient_number: str, limit: int = 500):
    patient_number = (patient_number or "").strip()
    if not patient_number:
        return []

    sql = """
    SELECT
      R.DatePerformed,
      R.ProcedureID,
      R.ParameterID,
      R.LabTestResults,
      R.Reference,
      H.PatientNumber,
      H.PatientStatus,
      D.DoctorName
    FROM labrequestheader H
    JOIN labresultdetail R
      ON H.LabRequestNumber = R.LabRequestNumber
    JOIN doctorinformation D
      ON D.DoctorID COLLATE utf8mb4_unicode_ci = H.DoctorID COLLATE utf8mb4_unicode_ci
    WHERE
      H.PatientNumber COLLATE utf8mb4_unicode_ci = %s COLLATE utf8mb4_unicode_ci
      AND R.LabTestResults IS NOT NULL
    ORDER BY R.DatePerformed DESC
    LIMIT %s
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (patient_number, int(limit)))
            return cur.fetchall()
    finally:
        conn.close()


# def fetch_patient_meta(patient_number: str):
    patient_number = (patient_number or "").strip()
    if not patient_number:
        return {}

    sql = """
    SELECT
        CompanyID,
        DepartmentID,
        CustomerID,
        CustomerName,
        CustomerAddress1,
        CustomerAddress2,
        CustomerAddress3,
        CustomerCity,
        CustomerCountry,
        CustomerPhone,
        CustomerEmail,
        CustomerWebPage,
        PatientCellPhone,
        PatientNumber,
        PatientName,
        Age,
        BirthDate,
        Gender,
        Height,
        BloodGroup
    FROM CustomerInformation
    WHERE PatientNumber = %s
    LIMIT 1;
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (patient_number,))
            return cur.fetchone() or {}
    finally:
        conn.close()


def fetch_patient_meta(patient_number: str):
    patient_number = (patient_number or "").strip()
    if not patient_number:
        return {}

    sql = """
    SELECT
        CompanyID,
        DepartmentID,
        CustomerID,
        CustomerName,
        CustomerAddress1,
        CustomerAddress2,
        CustomerAddress3,
        CustomerCity,
        CustomerCountry,
        CustomerPhone,
        CustomerEmail,
        CustomerWebPage,
        PatientCellPhone,
        PatientNumber,
        PatientName,
        Age,
        BirthDate,
        Gender,
        Height,
        BloodGroup
    FROM CustomerInformation
    WHERE PatientNumber COLLATE utf8mb4_unicode_ci = %s COLLATE utf8mb4_unicode_ci
    LIMIT 1
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (patient_number,))
            return cur.fetchone() or {}
    finally:
        conn.close()

def search_patients(q: str, limit: int = 50):
    q = (q or "").strip()
    if not q:
        return []

    limit = min(int(limit or 50), 200)

    # Small normalization for phone searches
    q_nospace = q.replace(" ", "")

    sql = """
    SELECT
        PatientNumber,
        PatientName,
        PatientCellPhone,
        Gender,
        Age,
        BirthDate,
        PatientType,
        PayableBy,
        RegistrationDate,
        LastVisited
    FROM CustomerInformation
    WHERE
        PatientNumber LIKE %s
        OR PatientCellPhone LIKE %s
        OR REPLACE(PatientCellPhone, ' ', '') LIKE %s
        OR PatientName LIKE %s
    ORDER BY LastVisited DESC
    LIMIT %s
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    q + "%",               # PatientNumber starts-with (uses index)
                    "%" + q + "%",         # phone contains
                    "%" + q_nospace + "%", # phone contains without spaces
                    "%" + q + "%",         # name contains
                    limit,
                ),
            )
            return cur.fetchall() or []
    finally:
        conn.close()


def search_patients_paged(
    q: str = "",
    date_field: str = "LastVisited",   # "LastVisited" or "RegistrationDate"
    date_from: str | None = None,      # "YYYY-MM-DD"
    date_to: str | None = None,        # "YYYY-MM-DD"
    page: int = 1,
    page_length: int = 50,
    sort_by: str = "LastVisited",
    sort_order: str = "DESC",
):
    q = (q or "").strip()
    page = max(int(page or 1), 1)
    page_length = min(max(int(page_length or 50), 1), 200)
    offset = (page - 1) * page_length

    # Allowlist ORDER BY columns (prevents SQL injection)
    allowed_sort = {
        "PatientNumber": "PatientNumber",
        "PatientName": "PatientName",
        "PatientCellPhone": "PatientCellPhone",
        "Age": "Age",
        "Gender": "Gender",
        "BirthDate": "BirthDate",
        "RegistrationDate": "RegistrationDate",
        "LastVisited": "LastVisited",
    }
    sort_by_sql = allowed_sort.get(sort_by, "LastVisited")
    sort_order_sql = "ASC" if (sort_order or "").upper() == "ASC" else "DESC"

    # Allowlist date field
    date_field_sql = "LastVisited" if date_field not in ("LastVisited", "RegistrationDate") else date_field

    where = []
    params: list = []

    # Search filters
    if q:
        q_nospace = q.replace(" ", "")
        where.append(
            "("
            "PatientNumber LIKE %s OR "
            "PatientCellPhone LIKE %s OR "
            "REPLACE(PatientCellPhone, ' ', '') LIKE %s OR "
            "PatientName LIKE %s"
            ")"
        )
        params.extend([q + "%", "%" + q + "%", "%" + q_nospace + "%", "%" + q + "%"])

    # Date range filter (inclusive for the whole day)
    # We do: >= date_from 00:00:00 AND < (date_to + 1 day) 00:00:00
    if date_from:
        df = getdate(date_from)
        where.append(f"{date_field_sql} >= %s")
        params.append(f"{df} 00:00:00")

    if date_to:
        dt = add_days(getdate(date_to), 1)
        where.append(f"{date_field_sql} < %s")
        params.append(f"{dt} 00:00:00")

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    # IMPORTANT: use the real table name as created: `customerinformation`
    count_sql = f"SELECT COUNT(*) AS cnt FROM customerinformation{where_sql}"

    data_sql = f"""
        SELECT
            PatientNumber,
            PatientName,
            PatientCellPhone,
            Gender,
            Age,
            BirthDate,
            PatientType,
            PayableBy,
            RegistrationDate,
            LastVisited
        FROM customerinformation
        {where_sql}
        ORDER BY {sort_by_sql} {sort_order_sql}
        LIMIT %s OFFSET %s
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(count_sql, tuple(params))
            total = (cur.fetchone() or {}).get("cnt", 0)

            cur.execute(data_sql, tuple(params + [page_length, offset]))
            rows = cur.fetchall() or []

        return {
            "total": int(total),
            "page": page,
            "page_length": page_length,
            "rows": rows,
        }
    finally:
        conn.close()




# reuse your existing get_conn() that returns pymysql.connect(...)
# from .smartfinancial import get_conn   # if get_conn is in this same file, ignore

def fetch_patient_vitals(patient_number: str, limit: int = 200):
    patient_number = (patient_number or "").strip()
    if not patient_number:
        return []

    limit = max(1, min(cint(limit), 1000))

    sql = """
        SELECT
            ch.CompanyID,
            ch.BranchID,
            ch.DepartmentID,
            ch.ServiceReference,
            ch.ServiceDate,
            ch.PatientNumber,
            ch.PatientName,
            cs.VitalStatistic,
            cs.Result,
            '' AS Remark,
            cs.VitalUOM,
            cs.DateRecorded
        FROM (
            SELECT
                CompanyID, BranchID, DepartmentID, ServiceReference,
                ServiceDate, PatientNumber, PatientName
            FROM consultationheader
            WHERE PatientNumber = %s
            ORDER BY ServiceDate DESC
            LIMIT 2000
        ) ch
        JOIN consultationstatistics cs
          ON cs.CompanyID = ch.CompanyID
         AND cs.BranchID = ch.BranchID
         AND cs.DepartmentID = ch.DepartmentID
         AND cs.ServiceReference = ch.ServiceReference
        ORDER BY COALESCE(cs.DateRecorded, ch.ServiceDate) DESC
        LIMIT %s
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (patient_number, limit))
            rows = cur.fetchall() or []

            if rows and isinstance(rows[0], dict):
                return rows

            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()


# Diagnostics
def fetch_patient_diagnostics(patient_no: str, limit: int = 300):
    patient_no = (patient_no or "").strip()
    if not patient_no:
        return []

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    H.ServiceDate,
                    H.ServiceReference,
                    H.ConsultDescription,
                    H.DateTimeIn,
                    H.DateTimeOut,
                    H.BranchName,
                    H.DepartmentID,
                    H.Room,
                    H.DoctorID,
                    D.DoctorName,
                    -- ✅ Canonical Chief Complaint
                    NULLIF(H.Symptoms, '') AS ChiefComplaint,
                    H.DiagnosisCategory,
                    H.Diagnosis,
                    H.ClinicalHpi,
                    H.ClinicalNotes,

                    H.Investigation,
                    H.InvestigationRemarks,
                    H.Treatment,
                    H.TreatmentRemarks,
                    H.Medication,
                    H.Management,

                    H.Status,
                    H.Invoiced,
                    H.PaidYN
                FROM ConsultationHeader H
                LEFT JOIN DoctorInformation D
                  ON D.DoctorID = H.DoctorID
                WHERE H.PatientNumber = %s
                ORDER BY H.ServiceDate DESC
                LIMIT %s
            """
            cur.execute(sql, (patient_no, int(limit)))
            return cur.fetchall() or []
    finally:
        conn.close()


# Medications 
def fetch_patient_medications(patient_no: str, limit: int = 300):
    patient_no = (patient_no or "").strip()
    if not patient_no:
        return []

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    H.ServiceReference,
                    H.ServiceDate,
                    H.PatientNumber,
                    H.PatientName,
                    D.DoctorName,

                    CP.ItemName,
                    CP.ItemID,
                    CP.Dosage,
                    CP.NoOfDays,
                    CP.Quantity,
                    CP.ItemUOM,
                    CP.Frequency,
                    CP.RouteID,
                    CP.InstrMsg
                FROM ConsultationHeader H
                INNER JOIN ConsultationPrescription CP
                    ON H.CompanyID = CP.CompanyID
                   AND H.BranchID = CP.BranchID
                   AND H.DepartmentID = CP.DepartmentID
                   AND H.ServiceReference = CP.ServiceReference
                LEFT JOIN DoctorInformation D
                    ON H.CompanyID = D.CompanyID
                   AND H.BranchID = D.BranchID
                   AND H.DepartmentID = D.DepartmentID
                   AND H.DoctorID = D.DoctorID
                WHERE
                    H.PatientNumber = %s
                ORDER BY H.ServiceDate DESC
                LIMIT %s
            """
            cur.execute(sql, (patient_no, int(limit)))
            return cur.fetchall() or []
    finally:
        conn.close()
