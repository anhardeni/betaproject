"""
Customs Status Log — Server-side controller (Refactored: High Performance & Anti-Hang)
======================================================================================
"""
import hashlib
import json
import base64
import copy
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date, add_days, nowdate

# ─── Master-status set ──────────────────────────────────────────────────────
# Tambahkan NPD di sini agar scheduler tetap bisa melacak jika admin bertindak
ACTIVE_STATUSES = {"Pending", "Registered", "On Hold", "Action Required: NPD"}

# Pisahkan NPD dari status penyelesaian
# Catatan: CEISA menggunakan kode numerik (misal 2703) dan string (misal SPPB) secara bergantian.
COMPLETED_RESPON_CODES = {
    "SPPB", "2703", # Surat Persetujuan Pengeluaran Barang
    "NPE", "2803",  # Nota Pelayanan Ekspor
    "SPPD", "2705", # Surat Persetujuan Pengeluaran Dokumen
    "3003", "2003", "2303", "4003"
}
# Kode Respon atau Status yang membutuhkan tindakan manual
ACTION_RESPON_CODES = {
    "NPD", "51315", # Nota Permintaan Data
    "SPJK",         # Surat Penetapan Jalur Kuning
    "SPJM",         # Surat Penetapan Jalur Merah
    "SPTNP", "440", "51328", # Surat Penetapan Tarif dan Nilai Pabean
    "KONSULTASI",
    "SPBL", "51313" # Surat Penetapan Barang Lartas
}
REJECTED_STATUS_CODES = {"TOLAK", "REJECT"}

# Lane Mapping (Jalur)
HIJAU_CODES = {"SPPB", "2703", "NPE", "2803"}
KUNING_CODES = {"SPJK"}
MERAH_CODES = {"SPJM", "SPTNP", "440", "51328", "SPBL", "51313"}

class CustomsStatusLog(Document):
    def validate(self):
        if not self.no_aju:
            frappe.throw("Nomor Aju wajib diisi pada Customs Status Log.")

    def autoname(self):
        self.name = self.no_aju

# ════════════════════════════════════════════════════════════════════════════
# Public methods & Triggers
# ════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_or_update_log(docname, no_aju, payload, bc_type=""):
    try:
        no_aju = str(no_aju).strip()
        if not no_aju:
            return {"status": "error", "message": "no_aju kosong."}

        payload_str = payload if isinstance(payload, str) else json.dumps(payload, default=str)

        if frappe.db.exists("Customs Status Log", no_aju):
            log = frappe.get_doc("Customs Status Log", no_aju)
        else:
            log = frappe.new_doc("Customs Status Log")
            log.no_aju = no_aju

        log.doctype_type = _map_bc_type(bc_type)
        log.linked_document_type = "HEADER V21"
        log.linked_document_name = docname if frappe.db.exists("HEADER V21", docname) else None
        log.submission_datetime = now_datetime()
        log.payload_json = payload_str

        if not log.bc_status:
            log.bc_status = "Pending"
            
        log.save(ignore_permissions=True, ignore_links=True)
        
        # Perlindungan ACID: Hanya commit jika tidak dipanggil dari dalam siklus on_submit dokumen lain
        if not (frappe.flags.in_insert or frappe.flags.in_save or frappe.flags.in_test):
            frappe.db.commit()

        # TRIGGER INSTAN: Langsung lempar ke worker tanpa menunggu scheduler (Fast feedback)
        frappe.enqueue(
            "singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log.pull_status_for_log",
            queue="short",
            log_name=log.name,
            job_id=f"ceisa_poll_init_{no_aju}",
            enqueue_after_commit=True
        )

        return {"status": "success", "log_name": log.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Create Log Error [{no_aju}]")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def pull_status_now(log_name):
    try:
        return pull_status_for_log(log_name)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Manual Pull Error [{log_name}]")
        return {"status": "error", "message": str(e)}


# ════════════════════════════════════════════════════════════════════════════
# Scheduler entry (Background Job Delegation)
# ════════════════════════════════════════════════════════════════════════════

def update_all_active_status():
    """HANYA mendelegasikan tugas, TIDAK melakukan request API di sini."""
    logs = frappe.get_all(
        "Customs Status Log",
        filters={
            "bc_status": ["in", list(ACTIVE_STATUSES)],
            "creation": [">", add_days(nowdate(), -30)]
        },
        fields=["name", "no_aju"]
    )

    frappe.logger("customs_status_log").info(
        f"Scheduler: memecah {len(logs)} antrean aktif ke Background Worker."
    )

    for log in logs:
        frappe.enqueue(
            "singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log.pull_status_for_log",
            queue="long",
            log_name=log.name,
            job_id=f"ceisa_poll_{log.no_aju}",
            enqueue_after_commit=True
        )


# ════════════════════════════════════════════════════════════════════════════
# Core Pull Logic (Safe Execution)
# ════════════════════════════════════════════════════════════════════════════

def pull_status_for_log(log_name):
    from singlecore_apps.api.ceisa_api.status import get_status_by_nomor_aju
    log = frappe.get_doc("Customs Status Log", log_name)
    no_aju = log.no_aju
    now = now_datetime()
    is_manual = not frappe.flags.is_scheduler
    updates = {} # Menampung semua field parent yang akan diupdate via DB query

    if not is_manual and log.next_polling_time and log.next_polling_time > now:
        return {"status": "skipped", "message": "Belum waktunya"}

    # Call API (Pastikan di modul ini 'requests.get' menggunakan timeout=(5,15))
    result = get_status_by_nomor_aju(no_aju)
    
    if result.get("status") != "success":
        new_interval = min((log.polling_interval or 5) * 2, 720)
        frappe.db.set_value("Customs Status Log", log_name, {
            "polling_interval": new_interval,
            "next_polling_time": add_to_date(now, minutes=new_interval)
        }, update_modified=True)
        return {"status": "api_error", "message": result.get("message")}

    data = result.get("data") or {}
    
    # CLOUDFLARE TRAP: Cegah parsing error berubah menjadi data kosong
    if isinstance(data, str):
        try: 
            data = json.loads(data)
        except Exception:
            new_interval = min((log.polling_interval or 5) * 2, 720)
            frappe.db.set_value("Customs Status Log", log_name, {
                "polling_interval": new_interval,
                "next_polling_time": add_to_date(now, minutes=new_interval)
            }, update_modified=True)
            return {"status": "api_error", "message": "Non-JSON response (Gateway Error)"}
    
    if not data.get("dataStatus") and isinstance(data.get("item"), dict): data = data.get("item")
    elif not data.get("dataStatus") and isinstance(data.get("data"), dict): data = data.get("data")

    # ANTI-OOM HASHING: Hapus payload PDF dari memory sebelum MD5
    data_for_hash = copy.deepcopy(data)
    for r in (data_for_hash.get("dataRespon") or []):
        r.pop("Pdf", None)
        r.pop("pdf", None)
        
    raw_data_string = json.dumps(data_for_hash, sort_keys=True, default=str)
    current_hash = hashlib.md5(raw_data_string.encode('utf-8')).hexdigest()

    is_working_hour = 8 <= now.hour <= 18
    is_weekend = now.weekday() >= 5
    
    if log.last_response_hash == current_hash and not is_manual:
        new_interval = min((log.polling_interval or 5) * 1.5, 360)
        if (not is_working_hour or is_weekend) and log.polling_priority != "High":
            new_interval = max(new_interval, 120)
            
        frappe.db.set_value("Customs Status Log", log_name, {
            "last_pull_datetime": now,
            "polling_interval": new_interval,
            "next_polling_time": add_to_date(now, minutes=new_interval)
        }, update_modified=True)
        return {"status": "no_change"}

    # Data Baru Terdeteksi
    updates.update({
        "last_response_raw": raw_data_string,
        "last_pull_datetime": now,
        "last_response_hash": current_hash,
        "polling_interval": 5,
        "next_polling_time": add_to_date(now, minutes=5),
        "bc_status": log.bc_status # default
    })

    # ── Process dataStatus[] (APPEND-ONLY PATTERN) ──
    added_statuses = 0
    for row in (data.get("dataStatus") or []):
        if _is_status_exist(log, row): continue
        kode = row.get("kodeStatus")
        ensure_status_code_exists("Referensi Status1", kode)

        # Suntik baris baru tanpa memanggil log.save()
        _append_child_row(log_name, "Customs Status Log Status", "statuses", {
            "nomor_aju": row.get("nomorAju"),
            "kode_status": kode,
            "nomor_daftar": row.get("nomorDaftar"),
            "tanggal_daftar": _parse_date(row.get("tanggalDaftar")),
            "waktu_status": _parse_datetime(row.get("waktuStatus")),
            "keterangan": row.get("keterangan"),
        })
        added_statuses += 1
        
        # STATE MACHINE: Update Status from status codes
        kode_status = str(kode or "").upper()
        if kode_status in ACTION_RESPON_CODES:
            updates["bc_status"] = "Action Required: NPD"

    # Header Data Fallbacks
    no_aju = data.get("nomorAju") or data.get("nomor_aju") or log.no_aju
    kode_dok = data.get("kodeDokumen") or str(log.doctype_type or "")
    if str(kode_dok).startswith("BC"): kode_dok = str(kode_dok).replace("BC", "", 1)
    updates["doctype_type"] = kode_dok

    # ── Process dataRespon[] (APPEND-ONLY PATTERN) ──
    added_responses = 0
    for row in (data.get("dataRespon") or []):
        existing_row = _get_response_row(log, row)
        kode = row.get("kodeRespon")
        
        if existing_row:
            api_pdf = row.get("Pdf") or row.get("pdf")
            if not existing_row.pdf_file and api_pdf:
                pdf_link = _save_pdf(api_pdf, no_aju, row, log_name)
                if pdf_link:
                    # Update child specific field only
                    frappe.db.set_value("Customs Status Log Response", existing_row.name, "pdf_file", pdf_link)
                    if existing_row.kode_respon in COMPLETED_RESPON_CODES:
                        _trigger_email_async(log, existing_row.kode_respon, pdf_link)
            continue

        kode = row.get("kodeRespon")
        ensure_status_code_exists("Referensi Respon1", kode) 

        pdf_data = row.get("Pdf") or row.get("pdf")
        pdf_link = _save_pdf(pdf_data, no_aju, row, log_name) if pdf_data else None
        
        _append_child_row(log_name, "Customs Status Log Response", "responses", {
            "nomor_aju": row.get("nomorAju"),
            "kode_respon": kode,
            "nomor_respon": row.get("nomorRespon"),
            "tanggal_respon": _parse_date(row.get("tanggalRespon")),
            "waktu_respon": _parse_datetime(row.get("waktuRespon")),
            "waktu_status": _parse_datetime(row.get("waktuStatus")),
            "keterangan": row.get("keterangan"),
            "pesan_json": json.dumps(row.get("pesan") or [], ensure_ascii=False),
            "pdf_file": pdf_link,
        })
        added_responses += 1

        # STATE MACHINE: Update Status
        kode_respon = str(kode or "").upper()
        if kode_respon in COMPLETED_RESPON_CODES and updates.get("bc_status") not in ("Completed", "Rejected"):
            updates["bc_status"] = "Completed"
            _trigger_email_async(log, kode_respon, pdf_link)
            
        elif kode_respon in ACTION_RESPON_CODES:
            updates["bc_status"] = "Action Required: NPD"

    # ── Finalizing ──
    _try_set_nopen(log, data, updates)
    _try_set_rejected(log, data, updates)

    # ── Lane Mapping (Jalur) ──
    found_jalur = None
    # Gabungkan respon dan status untuk mencari 'Jalur' terbaru
    combined_rows = (data.get("dataRespon") or []) + (data.get("dataStatus") or [])
    
    # Ambil kode terakhir yang cocok dengan pemetaan jalur (asumsi urutan kronologis)
    for row in reversed(combined_rows):
        code = str(row.get("kodeRespon") or row.get("kodeStatus") or "").upper()
        if code in MERAH_CODES:
            found_jalur = "Merah"
            break
        elif code in KUNING_CODES:
            found_jalur = "Kuning"
            break
        elif code in HIJAU_CODES:
            found_jalur = "Hijau"
            break
            
    if found_jalur:
        updates["jalur"] = found_jalur

    # Terapkan update Parent secara simultan (Anti-Deadlock)
    frappe.db.set_value("Customs Status Log", log_name, updates, update_modified=True)
    frappe.db.commit() # Aman, dipanggil mandiri oleh worker
    
    # Reload log memory state for doc syncing
    log.reload()
    _sync_linked_doc(log)

    return {"status": "success", "no_aju": no_aju, "added_responses": added_responses}


# ════════════════════════════════════════════════════════════════════════════
# Helpes (I/O, File, Async logic)
# ════════════════════════════════════════════════════════════════════════════

def _append_child_row(parent_name, doctype_name, parentfield, payload):
    """Menyuntik child table secara diam-diam tanpa memicu Delete-Insert Induk."""
    last_idx = frappe.db.get_value(doctype_name, {"parent": parent_name}, "max(idx)") or 0
    new_doc = frappe.new_doc(doctype_name)
    new_doc.update(payload)
    new_doc.parent = parent_name
    new_doc.parenttype = "Customs Status Log"
    new_doc.parentfield = parentfield
    new_doc.idx = last_idx + 1
    new_doc.insert(ignore_permissions=True)


def _save_pdf(base64_or_path, nomor_aju, api_row, doc_name):
    """Save PDF dengan proteksi duplikasi storage (Inode exhaustion)."""
    try:
        kode = str(api_row.get("kodeRespon") or "RESPON").replace("/", "-")
        nomor = str(api_row.get("nomorRespon") or frappe.generate_hash(length=6)).replace("/", "-")
        fname = "".join(x for x in f"CEISA_{nomor_aju}_{kode}_{nomor}.pdf" if x.isalnum() or x in "._-")

        # PROTEKSI DUPLIKASI STORAGE
        existing_file = frappe.db.get_value("File", {"file_name": fname, "attached_to_name": doc_name}, "name")
        if existing_file:
            return existing_file

        field_value = str(base64_or_path).strip()
        if "/" in field_value and field_value.endswith(".pdf"):
            from singlecore_apps.api.ceisa_api.status import download_respon
            res = download_respon(field_value)
            if res.get("status") != "success": return None
            pdf_bytes = res.get("data")
        else:
            if "," in field_value: field_value = field_value.split(",", 1)[1]
            pdf_bytes = base64.b64decode(field_value)

        from frappe.utils.file_manager import save_file
        return save_file(fname, pdf_bytes, "Customs Status Log", doc_name, is_private=1, decode=False).name
    except Exception:
        return None


def _trigger_email_async(log, kode_respon, pdf_link):
    """Gunakan modul pengirim yang sudah memiliki mekanisme sendmail antrean (now=False)"""
    try:
        from singlecore_apps.api.ceisa_api.status import send_completion_notification
        # Lempar email ke background queue agar tidak mem-blok worker saat SMTP lambat
        frappe.enqueue(
            send_completion_notification,
            queue="short",
            log=log,
            row={"kodeRespon": kode_respon, "pdf_file": pdf_link}
        )
    except Exception as e:
        frappe.log_error(str(e), "Async Email Error")

def _is_status_exist(log_doc, api_row):
    kode, waktu = str(api_row.get("kodeStatus") or ""), str(api_row.get("waktuStatus") or "")
    return any(str(r.kode_status or "") == kode and str(r.waktu_status or "") == waktu for r in (log_doc.statuses or []))

def _get_response_row(log_doc, api_row):
    nomor, tgl = str(api_row.get("nomorRespon") or ""), str(api_row.get("tanggalRespon") or "")
    kode, waktu = str(api_row.get("kodeRespon") or ""), str(api_row.get("waktuRespon") or "")
    for r in (log_doc.responses or []):
        if nomor and tgl and str(r.nomor_respon or "") == nomor and str(r.tanggal_respon or "") == tgl: return r
        if not (nomor and tgl) and str(r.kode_respon or "") == kode and str(r.waktu_respon or "") == waktu: return r
    return None

def _try_set_nopen(log_doc, api_data, updates):
    if log_doc.nopen or updates.get("nopen"): return
    for source in ["dataStatus", "dataRespon"]:
        for row in (api_data.get(source) or []):
            if row.get("nomorDaftar") and row.get("tanggalDaftar"):
                updates["nopen"] = str(row.get("nomorDaftar"))
                updates["nopen_date"] = _parse_date(row.get("tanggalDaftar"))
                if updates.get("bc_status", log_doc.bc_status) not in ("Completed", "Rejected"):
                    updates["bc_status"] = "Registered"
                return

def _try_set_rejected(log_doc, api_data, updates):
    if updates.get("bc_status", log_doc.bc_status) in ("Completed", "Rejected"): return
    for row in (api_data.get("dataStatus") or []):
        if str(row.get("kodeStatus") or "").upper() in REJECTED_STATUS_CODES or "TOLAK" in str(row.get("keterangan") or "").upper():
            updates["bc_status"] = "Rejected"
            return

def _sync_linked_doc(log_doc):
    if not (log_doc.linked_document_type == "HEADER V21" and frappe.db.exists("HEADER V21", log_doc.linked_document_name)):
        return
    try:
        # Gunakan set_value update pada header untuk cegah deadlock transaksi UI
        updates = {}
        header_nopen, header_date, header_aju = frappe.db.get_value("HEADER V21", log_doc.linked_document_name, ["nomor_daftar", "tanggal_daftar", "nomoraju"])
        
        if log_doc.nopen and header_nopen != log_doc.nopen: updates["nomor_daftar"] = log_doc.nopen
        if log_doc.nopen_date and str(header_date or "") != str(log_doc.nopen_date or ""): updates["tanggal_daftar"] = log_doc.nopen_date
        if log_doc.no_aju and not header_aju: updates["nomoraju"] = log_doc.no_aju
        
        if updates:
            frappe.db.set_value("HEADER V21", log_doc.linked_document_name, updates, update_modified=True)
    except Exception as e:
        frappe.log_error(str(e), "Sync Linked Doc Error")

def ensure_status_code_exists(doctype, code):
    if not code: return
    try:
        if not frappe.db.exists("DocType", doctype): return
        if frappe.db.exists(doctype, code): return
        meta = frappe.get_meta(doctype)
        field_to_check = None
        if meta.get_field("kode_respon"): field_to_check = "kode_respon"
        elif meta.get_field("code"): field_to_check = "code"
        elif meta.get_field("kode_status"): field_to_check = "kode_status"
        if field_to_check and frappe.db.exists(doctype, {field_to_check: code}): return
        new_doc = frappe.new_doc(doctype)
        if field_to_check: new_doc.set(field_to_check, code)
        if meta.get_field("uraian_respon"): new_doc.uraian_respon = "Diatur Otomatis Sistem"
        elif meta.get_field("nama_status"): new_doc.nama_status = "Diatur Otomatis Sistem"
        elif meta.get_field("description"): new_doc.description = "Auto-created from API"
        if not new_doc.name: new_doc.name = code
        new_doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.logger("customs_status_log").warning(f"Gagal memastikan status code {code} di {doctype}: {e}")

def _parse_date(val):
    if not val: return None
    val = str(val).strip()
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y%m%d", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            from datetime import datetime as _dt
            return _dt.strptime(val[:10], fmt).strftime("%Y-%m-%d")
        except ValueError: continue
    return val[:10] if len(val) >= 10 else None

def _parse_datetime(val):
    if not val: return None
    val = str(val).strip().replace("T", " ")
    for sep in ("+", "Z"): val = val.split(sep)[0]
    val = val[:19]
    try:
        from datetime import datetime as _dt
        return _dt.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception: return None

def _map_bc_type(kode_dokumen):
    mapping = {"20": "PIB", "200": "PIB", "30": "PEB", "300": "PEB", "23": "BC23", "25": "BC25", "27": "BC27", "261": "PIB", "262": "PIB"}
    return mapping.get(str(kode_dokumen), str(kode_dokumen)[:5] if kode_dokumen else "")
