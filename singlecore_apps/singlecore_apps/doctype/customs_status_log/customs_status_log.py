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
import hashlib
import json
import base64
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, today, add_to_date, get_datetime, add_days, nowdate

# ─── Master-status set that requires continued polling ──────────────────────
ACTIVE_STATUSES = {"Pending", "Registered", "On Hold"}

# ─── kodeRespon values that indicate final-release / completed ───────────────
COMPLETED_RESPON_CODES = {"SPPB", "NPE", "SPPD"}  # adjust to real codes, SPBL dihapus karena statusnya belum pasti/final

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

    except Exception as e:
        msg = str(e)
        frappe.log_error(
            frappe.get_traceback(),
            f"Customs Status Log — create_or_update_log [{no_aju}]"
        )
        return {"status": "error", "message": msg}


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
        filters={
            "bc_status": ["in", list(ACTIVE_STATUSES)],
            "creation": [">", add_days(nowdate(), -30)] # Hanya 30 hari terakhir
        },
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
    Expert Smart Polling Integration:
    - Hash Comparison (Deteksi perubahan data)
    - Adaptive Intervals (Jeda dinamis)
    - Working Hours Awareness (Hemat API di malam hari)
    - Tetap menjalankan fungsi asli: dataStatus, dataRespon, PDF, Nopen
    """
    from singlecore_apps.api.ceisa_api.status import get_status_by_nomor_aju
    log = frappe.get_doc("Customs Status Log", log_name)
    no_aju = log.no_aju
    now = now_datetime()
    # --- 1. SCHEDULER CHECK ---
    # Jika dipanggil otomatis (scheduler) dan belum waktunya, lewati.
    is_manual = not frappe.flags.is_scheduler
    if not is_manual and log.next_polling_time and log.next_polling_time > now:
        return {"status": "skipped", "message": "Belum waktunya polling"}
    # --- 2. CALL API CEISA ---
    result = get_status_by_nomor_aju(no_aju)
    
    # Handle Error API & Exponential Backoff
    if result.get("status") != "success":
        # Jika error, lipat gandakan jeda (max 12 jam)
        new_interval = min((log.polling_interval or 5) * 2, 720)
        log.db_set({
            "polling_interval": new_interval,
            "next_polling_time": add_to_date(now, minutes=new_interval),
        })
        return {"status": "api_error", "message": result.get("message")}
    data = result.get("data") or {}
    if isinstance(data, str):
        try: data = json.loads(data)
        except: data = {}
    # --- 3. DATA CHANGE DETECTION (HASHING) ---
    raw_data_string = json.dumps(data, sort_keys=True, default=str)
    current_hash = hashlib.md5(raw_data_string.encode('utf-8')).hexdigest()
    # Logic Jeda Malam/Weekend
    is_working_hour = 8 <= now.hour <= 18
    is_weekend = now.weekday() >= 5
    
    if log.last_response_hash == current_hash and not is_manual:
        # DATA SAMA & Scheduler mode: Tidak ada update dari Bea Cukai.
        # Naikkan interval perlahan (perkalian 1.5x)
        base_interval = log.polling_interval or 5
        new_interval = min(base_interval * 1.5, 360) # Max 6 jam
        
        # Jika di luar jam kerja, paksa jeda minimal 2 jam
        if (not is_working_hour or is_weekend) and log.polling_priority != "High":
            new_interval = max(new_interval, 120)
        log.db_set({
            "last_pull_datetime": now,
            "polling_interval": new_interval,
            "next_polling_time": add_to_date(now, minutes=new_interval)
        })
        return {"status": "no_change", "no_aju": no_aju}
    # --- 4. DATA BARU TERDETEKSI: LANJUT PROSES ASLI ---
    # Simpan raw response & metadata baru
    log.last_response_raw = raw_data_string
    log.last_pull_datetime = now
    log.last_response_hash = current_hash
    log.polling_interval = 5 # Reset ke 5 menit karena sedang aktif
    log.next_polling_time = add_to_date(now, minutes=5)
    log.retry_count = 0
    # ── Process dataStatus[] (Logika Asli Anda) ──────────────────────────
    added_statuses = 0
    for row in (data.get("dataStatus") or []):
        if _is_status_exist(log, row): continue
        
        # Pastikan kode status ada di master referensi
        kode = row.get("kodeStatus")
        ensure_status_code_exists("Referensi Status", kode)

        log.append("statuses", {
            "nomor_aju":    row.get("nomorAju"),
            "kode_status":  kode,
            "nomor_daftar": row.get("nomorDaftar"),
            "tanggal_daftar": _parse_date(row.get("tanggalDaftar")),
            "waktu_status": _parse_datetime(row.get("waktuStatus")),
            "keterangan":   row.get("keterangan"),
        })
        added_statuses += 1
    # ── Process dataRespon[] ─────────────────────────────────────────────
    added_responses = 0
    for row in (data.get("dataRespon") or []):
        existing_row = _get_response_row(log, row)
        
        # Jika baris sudah ada, cek apakah PDF-nya masih kosong dan API punya PDF baru
        if existing_row:
            api_pdf = row.get("Pdf") or row.get("pdf")
            if not existing_row.pdf_file and api_pdf:
                pdf_link = _save_pdf(api_pdf, no_aju, row, log.name)
                if pdf_link:
                    existing_row.pdf_file = pdf_link
                    frappe.logger("customs_status_log").info(f"PDF ditambahkan ke respon eksisting: {no_aju}")
            continue

        kode = row.get("kodeRespon")
        # Pastikan kode respon ada di master referensi (Referensi Respon)
        ensure_status_code_exists("Referensi Respon", kode) 

        pdf_data = row.get("Pdf") or row.get("pdf")
        pdf_link = None
        if pdf_data:
            pdf_link = _save_pdf(pdf_data, no_aju, row, log.name)
        
        log.append("responses", {
            "nomor_aju":     row.get("nomorAju"),
            "kode_respon":   kode,
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
        # --- START INSERT LOGIKA EMAIL DI SINI ---
            try:
                    # 'row' berisi dictionary respons API dari perulangan for,
                    # yang di dalamnya sudah terdapat url 'pdf_link' yang akan dikirim via email.
                    from singlecore_apps.api.ceisa_api.status import send_completion_notification
                    
                    # Agar baris ini tahu di mana pdf_link untuk attachment-nya
                    row["pdf_file"] = pdf_link 
                    send_completion_notification(log, row)
                    frappe.logger("customs_status_log").info(f"Trigger Email SPPB untuk Aju {no_aju} berhasil dipanggil.")
                
            except Exception as e:
                    # Amankan scheduler dari error jika gagal kirim email (misal: setting SMTP belum diatur)
                    frappe.log_error(title="Gagal Mengirim Email SPPB/NPE", message=str(e))
        # --- END LOGIKA EMAIL DI SINI ---
    # ── Finalizing (Nopen, Rejection, Sync) ──────────────────────────────
    _try_set_nopen(log, data)
    _try_set_rejected(log, data)
    # Simpan Header (Akan memicu Server Script update Batch otomatis)
    log.save(ignore_permissions=True)
    frappe.db.commit()
    _sync_linked_doc(log)

    return {
        "status": "success",
        "no_aju": no_aju,
        "added_statuses": added_statuses,
        "added_responses": added_responses,
        "bc_status": log.bc_status
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


def _get_response_row(log_doc, api_row):
    """
    Return the existing Row object from log_doc.responses if it matches api_row.
    Otherwise return None.
    Unique key: nomor_respon + tanggal_respon (or kode_respon+waktu_respon fallback).
    """
    nomor  = str(api_row.get("nomorRespon") or "")
    tgl    = str(api_row.get("tanggalRespon") or "")
    kode   = str(api_row.get("kodeRespon") or "")
    waktu  = str(api_row.get("waktuRespon") or "")

    for row in (log_doc.responses or []):
        if nomor and tgl:
            if str(row.nomor_respon or "") == nomor and str(row.tanggal_respon or "") == tgl:
                return row
        else:
            # fallback: kode_respon + waktu_respon
            if str(row.kode_respon or "") == kode and str(row.waktu_respon or "") == waktu:
                return row
    return None


# ════════════════════════════════════════════════════════════════════════════
# PDF helper
# ════════════════════════════════════════════════════════════════════════════

def _save_pdf(base64_or_path, nomor_aju, api_row, doc_name):
    """
    Automatic detection: if it's a path, download it. If it's base64, decode it.
    """
    try:
        if not base64_or_path:
            return None

        kode   = str(api_row.get("kodeRespon") or "RESPON").replace("/", "-")
        nomor  = str(api_row.get("nomorRespon") or frappe.generate_hash(length=6)).replace("/", "-")
        fname  = f"CEISA_{nomor_aju}_{kode}_{nomor}.pdf"

        # Hilangkan karakter ilegal lainnya untuk nama file
        fname = "".join(x for x in fname if x.isalnum() or x in "._-")

        field_value = str(base64_or_path).strip()
        pdf_bytes = None

        # 1. Check if it's a Path (e.g. 'respon/2026/4/20/...xxx.pdf')
        if "/" in field_value and field_value.endswith(".pdf"):
            from singlecore_apps.api.ceisa_api.status import download_respon
            frappe.logger("customs_status_log").info(f"Downloading PDF from path: {field_value}")
            res = download_respon(field_value)
            
            if res.get("status") == "success":
                pdf_bytes = res.get("data")
            else:
                err_ext = res.get("message") or "Unknown"
                # Simpan error ke DB agar user bisa baca di baris tersebut
                frappe.db.set_value("Customs Status Log Response", api_row.get("name"), "keterangan", f"ERR: {err_ext[:200]}")
                frappe.db.commit()
                return None
        
        # 2. Otherwise treat as Base64
        else:
            if "," in field_value:
                field_value = field_value.split(",", 1)[1]
            pdf_bytes = base64.b64decode(field_value)

        if not pdf_bytes:
            return None

        from frappe.utils.file_manager import save_file
        _file = save_file(
            fname, 
            pdf_bytes, 
            "Customs Status Log", 
            doc_name, 
            is_private=1,
            decode=False
        )
        
        frappe.db.commit()
        return _file.name

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            f"PDF Save Error [{nomor_aju[:20]}]"
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

def ensure_status_code_exists(doctype, code):
    """
    Mengecek apakah kode ada di referensi, jika tidak ada, buat otomatis
    agar log.save() tidak error (terutama untuk Link field).
    """
    if not code: return
    
    try:
        if not frappe.db.exists("DocType", doctype):
            return
            
        # 1. Cek berdasarkan Name (Primary Key)
        if frappe.db.exists(doctype, code):
            return
            
        # 2. Cek berdasarkan Field (kode_respon / kode_status / code)
        meta = frappe.get_meta(doctype)
        field_to_check = None
        if meta.get_field("kode_respon"): field_to_check = "kode_respon"
        elif meta.get_field("code"): field_to_check = "code"
        elif meta.get_field("kode_status"): field_to_check = "kode_status"
        
        if field_to_check and frappe.db.exists(doctype, {field_to_check: code}):
            return

        # 3. Buat Baru jika benar-benar tidak ada
        new_doc = frappe.new_doc(doctype)
        
        # Map code ke field yang sesuai
        if field_to_check:
            new_doc.set(field_to_check, code)
        
        # Map deskripsi default
        if meta.get_field("uraian_respon"):
            new_doc.uraian_respon = "Diatur Otomatis Sistem"
        elif meta.get_field("nama_status"):
            new_doc.nama_status = "Diatur Otomatis Sistem"
        elif meta.get_field("description"):
            new_doc.description = "Auto-created from API"
        
        # Gunakan code sebagai name jika autoname mengizinkan
        if not new_doc.name:
            new_doc.name = code
            
        new_doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.logger("customs_status_log").warning(f"Gagal memastikan status code {code} di {doctype}: {e}")


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
