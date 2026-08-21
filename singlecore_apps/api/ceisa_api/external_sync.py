# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.utils import now_datetime, add_to_date, flt, cint
from singlecore_apps.api.ceisa_api.auth import get_ceisa_settings, ensure_login, build_auth_headers

def smart_ceisa_polling():
    """
    Fungsi Penjadwal Otomatis (Anti-DDoS)
    Berjalan via Frappe Scheduler (Hourly)
    """
    # Mencari dokumen eksternal (Subkon/PPJK) yang belum selesai
    pending_logs = frappe.get_all("Customs Status Log", 
        filters={
            "is_external_doc": 1,
            "bc_status": ["in", ["Pending", "Registered", "On Hold"]],
            "next_polling_time": ["<=", now_datetime()]
        }, 
        fields=["name", "no_aju"]
    )

    for entry in pending_logs:
        try:
            # Menggunakan background worker agar satu dokumen gagal tidak mematikan antrean lain
            frappe.enqueue(
                "singlecore_apps.api.ceisa_api.external_sync.trigger_sync_now",
                log_name=entry.name,
                now=frappe.flags.in_test
            )
        except Exception:
            frappe.log_error(f"Failed to enqueue sync for {entry.no_aju}")


@frappe.whitelist()
def trigger_sync_now(log_name):
    """
    Penarik Data Detail Dokumen (API GET /document/detail).
    Pilar utama untuk menarik data dokumen yang diajukan pihak Subkon.
    """
    log = frappe.get_doc("Customs Status Log", log_name)
    no_aju = log.no_aju
    
    try:
        # 1. AUTH & SETTINGS
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        
        # Clean doc_type to get a clean number (e.g. BC27 -> 27)
        doc_type_clean = str(log.doctype_type or '27').upper().replace("BC", "").strip()
        
        # Format API: /openapi/document/detail/{jenisDokumen}/{no_aju}/{kantor}
        url = f"{base_url}/openapi/document/detail/{doc_type_clean}/{no_aju}/{log.kode_kantor}"
        headers = build_auth_headers(token)
        
        # 2. CALL API
        response = requests.get(url, headers=headers, timeout=30)
        
        # Handle 401 token refresh once
        if response.status_code == 401:
            from .auth import refresh_token
            new_token = refresh_token()
            if new_token:
                headers = build_auth_headers(new_token)
                response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            api_data = response.json()
            # 3. PROSES DATA KE DATABASE
            process_ceisa_detail_to_db(log, api_data.get("data") or api_data)
            
            # Jika data detail berhasil ditarik, hentikan polling terjadwal
            log.bc_status = "Completed" if not log.nopen else "Registered"
            log.next_polling_time = None
            log.save(ignore_permissions=True)
            frappe.db.commit()
            
            return True, f"Data {no_aju} berhasil ditarik dan di-sync."
        
        else:
            # 4. DATA BELUM TERBIT / ERROR (SMART BACKOFF)
            _handle_polling_error(log)
            return False, f"API Response {response.status_code}: Data belum tersedia."

    except frappe.ValidationError as e:
        _handle_polling_error(log)
        return False, str(e)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Sync External Error: {no_aju}")
        return False, str(e)


def _handle_polling_error(log):
    """Meningkatkan jeda polling secara bertahap jika data tidak ditemukan"""
    interval = log.polling_interval or 1
    new_interval = min(interval + 2, 24) # Maksimal 24 jam sekali
    
    log.db_set({
        "polling_interval": new_interval,
        "next_polling_time": add_to_date(now_datetime(), hours=new_interval),
        "bc_status": "Pending"
    })


def process_ceisa_detail_to_db(log, data):
    """
    Pemetaan (Mapping) Detail Dokumen dari JSON API ke Dokumen Internal.
    Optimized to upsert stand-alone BARANG V1 with bulk pre-fetching and dirty-checking.
    """
    # Normalize data (it is a list of one item from the live API)
    if isinstance(data, list) and len(data) > 0:
        doc_data = data[0]
    elif isinstance(data, dict):
        doc_data = data
    else:
        doc_data = {}

    barang_data = doc_data.get("barang", [])
    
    # Update Nopen di Log agar Laporan IT Inventory Sinkron
    log.nopen = doc_data.get("nomorDaftar") or log.nopen
    log.nopen_date = doc_data.get("tanggalDaftar") or log.nopen_date
    
    # 1. UPSERT HEADER V21
    if not frappe.db.exists("HEADER V21", log.no_aju):
        h = frappe.new_doc("HEADER V21")
        h.nomoraju = log.no_aju
        h.name = log.no_aju
        h.flags.name_set = True
        h.kode_dokumen = str(log.doctype_type or "").upper().replace("BC", "").strip()
        
        # Get entity name from 'entitas' list
        entitas_list = doc_data.get("entitas", [])
        nama_entitas = "External Partner"
        for ent in entitas_list:
            if ent.get("namaEntitas"):
                nama_entitas = ent.get("namaEntitas")
                break
        h.nama_entitas = nama_entitas
        
        h.nomor_daftar = log.nopen
        h.tanggal_daftar = log.nopen_date
        h.custom_is_external = 1
        h.insert(ignore_permissions=True)
    else:
        h = frappe.get_doc("HEADER V21", log.no_aju)
        h.nomor_daftar = log.nopen
        h.tanggal_daftar = log.nopen_date
        h.save(ignore_permissions=True)

    # 2. UPSERT BARANG V1 (STANDALONE)
    # Pre-fetch existing BARANG V1 records to avoid N+1 DB queries
    existing_barang = frappe.get_all("BARANG V1", filters={"nomoraju": h.name}, fields=["name", "seri_barang"])
    barang_map = {cint(b.seri_barang): b.name for b in existing_barang}
    
    for item in barang_data:
        seri = cint(item.get("seriBarang") or item.get("seri"))
        if not seri: continue
        
        existing_name = barang_map.get(seri)
        if existing_name:
            b_doc = frappe.get_doc("BARANG V1", existing_name)
        else:
            b_doc = frappe.new_doc("BARANG V1")
            b_doc.nomoraju = h.name
            b_doc.seri_barang = seri

        # Map fields and check if dirty
        is_dirty = False
        fields_to_map = {
            "kode_barang": item.get("kodeBarang"),
            "uraian": item.get("uraian"),
            "jumlah_satuan": flt(item.get("jumlahSatuan") or item.get("jumlah")),
            "kode_satuan": item.get("kodeSatuanBarang") or item.get("kodeSatuan"),
            "harga_satuan": flt(item.get("hargaSatuan") or item.get("harga"))
        }
        
        for fieldname, val in fields_to_map.items():
            if str(b_doc.get(fieldname) if b_doc.get(fieldname) is not None else "") != str(val if val is not None else ""):
                b_doc.set(fieldname, val)
                is_dirty = True
                
        if is_dirty or b_doc.is_new():
            b_doc.flags.ignore_links = True
            b_doc.flags.ignore_permissions = True
            b_doc.save(ignore_permissions=True)
            
    frappe.db.commit()
