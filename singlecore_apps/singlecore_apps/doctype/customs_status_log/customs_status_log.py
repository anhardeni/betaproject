"""
Customs Status Log — Server-side controller
============================================

Handles:
  - create_or_update_log()    : called after send_document() succeeds
  - pull_status_now()         : whitelisted manual trigger (Pull Status Now button)
  - update_all_active_status(): scheduler entry (hourly)
  - pull_status_for_log()     : core pull + parse + persist logic
  - _is_status_exist()        : idempotency check for dataStatus rows
  - _is_response_exist()      : idempotency check for dataRespon rows
  - _save_pdf()               : decode base64 PDF → private File
  - _sync_linked_doc()        : mirror nopen/nopen_date to linked HEADER V21

All API calls are wrapped in try/except and logged via frappe.log_error.
The scheduler is idempotent: running it multiple times must not create
duplicate rows in the child tables.
"""

import json
import base64
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, today

# ─── Master-status set that requires continued polling ──────────────────────
ACTIVE_STATUSES = {"Pending", "Registered", "On Hold"}

# ─── kodeRespon values that indicate final-release / completed ───────────────
COMPLETED_RESPON_CODES = {"SPPB", "NPE", "SPBL"}  # adjust to real codes

# ─── kodeStatus / keterangan patterns for rejection ─────────────────────────
REJECTED_STATUS_CODES = {"TOLAK", "REJECT"}


# ════════════════════════════════════════════════════════════════════════════
# DocType controller
# ════════════════════════════════════════════════════════════════════════════

class CustomsStatusLog(Document):
    def validate(self):
        if not self.no_aju:
            frappe.throw("Nomor Aju wajib diisi pada Customs Status Log.")

    def autoname(self):
        self.name = self.no_aju


# ════════════════════════════════════════════════════════════════════════════
# Public whitelisted methods
# ════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_or_update_log(docname, no_aju, payload, bc_type=""):
    """
    Create (or update) one Customs Status Log record after a successful
    submission to Bea Cukai.

    Args:
        docname  : HEADER V21 document name
        no_aju   : Nomor Aju returned by the API
        payload  : JSON payload that was sent (dict or str)
        bc_type  : kode_dokumen value (e.g. 'BC25', 'BC27', ...)

    Returns:
        dict with status and log_name
    """
    try:
        no_aju = str(no_aju).strip()
        if not no_aju:
            return {"status": "error", "message": "no_aju kosong, tidak dapat membuat log."}

        payload_str = payload if isinstance(payload, str) else json.dumps(payload, default=str)

        if frappe.db.exists("Customs Status Log", no_aju):
            log = frappe.get_doc("Customs Status Log", no_aju)
        else:
            log = frappe.new_doc("Customs Status Log")
            log.no_aju = no_aju

        # Map kode_dokumen → doctype_type select option
        log.doctype_type    = _map_bc_type(bc_type)
        log.linked_document_type = "HEADER V21"
        log.linked_document_name = docname
        log.submission_datetime  = now_datetime()
        log.payload_json         = payload_str

        if not log.bc_status:
            log.bc_status = "Pending"

        log.save(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "log_name": log.name}

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Customs Status Log — create_or_update_log [{no_aju}]"
        )
        return {"status": "error", "message": frappe.get_last_doc("Error Log").error if True else "Lihat Error Log"}


@frappe.whitelist()
def pull_status_now(log_name):
    """
    Manual trigger: Pull Status Now button in Customs Status Log form.

    Args:
        log_name: name of the Customs Status Log record

    Returns:
        dict with status and summary of changes
    """
    try:
        return pull_status_for_log(log_name)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Customs Status Log — pull_status_now [{log_name}]"
        )
        return {"status": "error", "message": "Error saat menarik status. Lihat Error Log."}


# ════════════════════════════════════════════════════════════════════════════
# Scheduler entry
# ════════════════════════════════════════════════════════════════════════════

def update_all_active_status():
    """
    Hourly scheduler function.
    Iterates all Customs Status Log records with bc_status in ACTIVE_STATUSES
    and pulls updated status from /status/{nomorAju}.
    """
    logs = frappe.get_all(
        "Customs Status Log",
        filters={"bc_status": ["in", list(ACTIVE_STATUSES)]},
        fields=["name", "no_aju"]
    )

    frappe.logger("customs_status_log").info(
        f"Scheduler: processing {len(logs)} active Customs Status Log records."
    )

    for log in logs:
        try:
            pull_status_for_log(log.name)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Customs Status Log — scheduler error [{log.no_aju}]"
            )


# ════════════════════════════════════════════════════════════════════════════
# Core pull logic
# ════════════════════════════════════════════════════════════════════════════

def pull_status_for_log(log_name):
    """
    Pull status from CEISA /status/{nomorAju}, parse dataStatus[] and
    dataRespon[], append new rows idempotently, set NOPEN, sync linked doc.

    Args:
        log_name: name of Customs Status Log

    Returns:
        dict with status, added_statuses, added_responses
    """
    from singlecore_apps.api.ceisa_api.status import get_status_by_nomor_aju

    log = frappe.get_doc("Customs Status Log", log_name)
    no_aju = log.no_aju

    # ── Call API ─────────────────────────────────────────────────────────
    result = get_status_by_nomor_aju(no_aju)
    if result.get("status") != "success":
        frappe.log_error(
            f"API error for no_aju={no_aju}: {result}",
            "Customs Status Log — pull_status_for_log"
        )
        return {"status": "api_error", "message": result.get("message", str(result))}

    data = result.get("data") or {}
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}

    # ── Save raw response for audit ───────────────────────────────────────
    log.last_response_raw = json.dumps(data, ensure_ascii=False, default=str)
    log.last_pull_datetime = now_datetime()

    # ── Process dataStatus[] ─────────────────────────────────────────────
    added_statuses = 0
    for row in (data.get("dataStatus") or []):
        if _is_status_exist(log, row):
            continue
        log.append("statuses", {
            "nomor_aju":    row.get("nomorAju"),
            "kode_status":  row.get("kodeStatus"),
            "nomor_daftar": row.get("nomorDaftar"),
            "tanggal_daftar": _parse_date(row.get("tanggalDaftar")),
            "waktu_status": _parse_datetime(row.get("waktuStatus")),
            "keterangan":   row.get("keterangan"),
        })
        added_statuses += 1

    # ── Process dataRespon[] ─────────────────────────────────────────────
    added_responses = 0
    for row in (data.get("dataRespon") or []):
        if _is_response_exist(log, row):
            continue

        pdf_link = None
        raw_pdf = row.get("Pdf") or ""
        if raw_pdf:
            pdf_link = _save_pdf(raw_pdf, no_aju, row, log.name)

        log.append("responses", {
            "nomor_aju":     row.get("nomorAju"),
            "kode_respon":   row.get("kodeRespon"),
            "nomor_daftar":  row.get("nomorDaftar"),
            "tanggal_daftar": _parse_date(row.get("tanggalDaftar")),
            "nomor_respon":  row.get("nomorRespon"),
            "tanggal_respon": _parse_date(row.get("tanggalRespon")),
            "waktu_respon":  _parse_datetime(row.get("waktuRespon")),
            "waktu_status":  _parse_datetime(row.get("waktuStatus")),
            "keterangan":    row.get("keterangan"),
            "pesan_json":    json.dumps(row.get("pesan") or [], ensure_ascii=False),
            "pdf_file":      pdf_link,
        })
        added_responses += 1

        # Check for completed status
        kode_respon = str(row.get("kodeRespon") or "").upper()
        if kode_respon in COMPLETED_RESPON_CODES and log.bc_status not in ("Completed", "Rejected"):
            log.bc_status = "Completed"

    # ── Determine NOPEN from dataStatus ──────────────────────────────────
    _try_set_nopen(log, data)

    # ── Check rejection ───────────────────────────────────────────────────
    _try_set_rejected(log, data)

    # ── Save header ───────────────────────────────────────────────────────
    log.save(ignore_permissions=True)
    frappe.db.commit()

    # ── Sync to linked document ───────────────────────────────────────────
    _sync_linked_doc(log)

    frappe.logger("customs_status_log").info(
        f"pull_status_for_log [{no_aju}]: +{added_statuses} status, +{added_responses} respon"
    )

    return {
        "status": "success",
        "no_aju": no_aju,
        "added_statuses": added_statuses,
        "added_responses": added_responses,
        "bc_status": log.bc_status,
        "nopen": log.nopen,
    }


# ════════════════════════════════════════════════════════════════════════════
# Deduplication helpers
# ════════════════════════════════════════════════════════════════════════════

def _is_status_exist(log_doc, api_row):
    """
    Return True if a matching row already exists in log_doc.statuses.
    Unique key: kode_status + waktu_status (both from API row).
    """
    kode   = str(api_row.get("kodeStatus") or "")
    waktu  = str(api_row.get("waktuStatus") or "")
    for row in (log_doc.statuses or []):
        if str(row.kode_status or "") == kode and str(row.waktu_status or "") == waktu:
            return True
    return False


def _is_response_exist(log_doc, api_row):
    """
    Return True if a matching row already exists in log_doc.responses.
    Unique key: nomor_respon + tanggal_respon (or kode_respon+waktu_respon fallback).
    """
    nomor  = str(api_row.get("nomorRespon") or "")
    tgl    = str(api_row.get("tanggalRespon") or "")
    kode   = str(api_row.get("kodeRespon") or "")
    waktu  = str(api_row.get("waktuRespon") or "")

    for row in (log_doc.responses or []):
        if nomor and tgl:
            if str(row.nomor_respon or "") == nomor and str(row.tanggal_respon or "") == tgl:
                return True
        else:
            # fallback: kode_respon + waktu_respon
            if str(row.kode_respon or "") == kode and str(row.waktu_respon or "") == waktu:
                return True
    return False


# ════════════════════════════════════════════════════════════════════════════
# PDF helper
# ════════════════════════════════════════════════════════════════════════════

def _save_pdf(base64_data, nomor_aju, api_row, doc_name):
    """
    Decode base64 PDF data and save as a private Frappe File.

    Args:
        base64_data: raw base64 string from API 'Pdf' field
        nomor_aju  : used in file naming
        api_row    : dict from dataRespon, used for naming
        doc_name   : Customs Status Log name (for attachment metadata)

    Returns:
        file_url (str) or None on failure
    """
    try:
        kode   = api_row.get("kodeRespon") or "RESPON"
        nomor  = api_row.get("nomorRespon") or frappe.generate_hash(length=6)
        fname  = f"CEISA_{nomor_aju}_{kode}_{nomor}.pdf"

        # Remove data-URL prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": fname,
            "attached_to_doctype": "Customs Status Log",
            "attached_to_name": doc_name,
            "content": base64.b64decode(base64_data),
            "is_private": 1,
        })
        _file.insert(ignore_permissions=True)
        frappe.db.commit()
        return _file.name  # Link → File uses doc name

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Customs Status Log — _save_pdf [{nomor_aju}]"
        )
        return None


# ════════════════════════════════════════════════════════════════════════════
# NOPEN / status-update helpers
# ════════════════════════════════════════════════════════════════════════════

def _try_set_nopen(log_doc, api_data):
    """
    Scan dataStatus[] for the first row with nomorDaftar + tanggalDaftar.
    If found — and header.nopen is not already set — populate nopen/nopen_date
    and set bc_status=Registered.
    """
    if log_doc.nopen:
        return  # already set, skip

    for row in (api_data.get("dataStatus") or []):
        nomor_daftar  = row.get("nomorDaftar")
        tanggal_daftar = row.get("tanggalDaftar")
        if nomor_daftar and tanggal_daftar:
            log_doc.nopen      = str(nomor_daftar)
            log_doc.nopen_date = _parse_date(tanggal_daftar)
            if log_doc.bc_status not in ("Completed", "Rejected"):
                log_doc.bc_status = "Registered"
            frappe.logger("customs_status_log").info(
                f"NOPEN set for {log_doc.no_aju}: {nomor_daftar} / {tanggal_daftar}"
            )
            break

    # Also check dataRespon[]
    if not log_doc.nopen:
        for row in (api_data.get("dataRespon") or []):
            nomor_daftar  = row.get("nomorDaftar")
            tanggal_daftar = row.get("tanggalDaftar")
            if nomor_daftar and tanggal_daftar:
                log_doc.nopen      = str(nomor_daftar)
                log_doc.nopen_date = _parse_date(tanggal_daftar)
                if log_doc.bc_status not in ("Completed", "Rejected"):
                    log_doc.bc_status = "Registered"
                break


def _try_set_rejected(log_doc, api_data):
    """
    Check dataStatus for known rejection codes and update bc_status accordingly.
    """
    if log_doc.bc_status in ("Completed", "Rejected"):
        return
    for row in (api_data.get("dataStatus") or []):
        kode = str(row.get("kodeStatus") or "").upper()
        ket  = str(row.get("keterangan") or "").upper()
        if kode in REJECTED_STATUS_CODES or "TOLAK" in ket or "REJECT" in ket:
            log_doc.bc_status = "Rejected"
            break


def _sync_linked_doc(log_doc):
    """
    Mirror nopen and nopen_date back to the linked HEADER V21 document.
    Silently skips if linked doc is not found or not HEADER V21.
    """
    if not (log_doc.linked_document_type and log_doc.linked_document_name):
        return
    if log_doc.linked_document_type != "HEADER V21":
        return
    if not frappe.db.exists("HEADER V21", log_doc.linked_document_name):
        return

    try:
        header = frappe.get_doc("HEADER V21", log_doc.linked_document_name)
        changed = False

        if log_doc.nopen and header.nomor_daftar != log_doc.nopen:
            header.nomor_daftar = log_doc.nopen
            changed = True
        if log_doc.nopen_date and str(header.tanggal_daftar or "") != str(log_doc.nopen_date or ""):
            header.tanggal_daftar = log_doc.nopen_date
            changed = True

        # Reflect nomoraju back if blank on the header
        if not header.nomoraju and log_doc.no_aju:
            header.nomoraju = log_doc.no_aju
            changed = True

        if changed:
            header.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.logger("customs_status_log").info(
                f"Synced HEADER V21 [{header.name}]: nopen={log_doc.nopen}"
            )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Customs Status Log — _sync_linked_doc [{log_doc.linked_document_name}]"
        )


# ════════════════════════════════════════════════════════════════════════════
# Utility / parse helpers
# ════════════════════════════════════════════════════════════════════════════

def _parse_date(val):
    """
    Safely parse various date string formats → 'YYYY-MM-DD' or None.
    Accepted: YYYY-MM-DD, DD-MM-YYYY, YYYYMMDD, DD/MM/YYYY, YYYY/MM/DD.
    """
    if not val:
        return None
    val = str(val).strip()
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y%m%d", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            from datetime import datetime as _dt
            return _dt.strptime(val[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback: return raw value if it looks like a date
    return val[:10] if len(val) >= 10 else None


def _parse_datetime(val):
    """
    Safely parse ISO-8601-ish datetime string → 'YYYY-MM-DD HH:MM:SS' or None.
    """
    if not val:
        return None
    val = str(val).strip().replace("T", " ")
    # drop timezone offset if present
    for sep in ("+", "Z"):
        val = val.split(sep)[0]
    val = val[:19]  # trim sub-seconds
    try:
        from datetime import datetime as _dt
        return _dt.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _map_bc_type(kode_dokumen):
    """Map kode_dokumen → doctype_type Select option (best-effort)."""
    mapping = {
        "20": "PIB", "200": "PIB",
        "30": "PEB", "300": "PEB",
        "23": "BC23",
        "25": "BC25",
        "27": "BC27",
        "261": "PIB", "262": "PIB",
    }
    return mapping.get(str(kode_dokumen), str(kode_dokumen)[:5] if kode_dokumen else "")
