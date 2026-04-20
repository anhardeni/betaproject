# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.utils import now_datetime, add_to_date, flt
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
        
        # Mapping endpoint sesuai tipe dokumen
        # Format API biasanya: /openapi/document/{tipe}/{no_aju}/{kantor}
        url = f"{base_url}/openapi/document/{log.doctype_type or 'BC27'}/{no_aju}/{log.kode_kantor}"
        headers = build_auth_headers(token)
        
        # 2. CALL API
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
    """
    header_data = data.get("header", {})
    barang_data = data.get("barang", [])
    
    # Update Nopen di Log agar Laporan IT Inventory Sinkron
    log.nopen = header_data.get("nomorDaftar") or log.nopen
    log.nopen_date = header_data.get("tanggalDaftar") or log.nopen_date
    
    # 1. UPSERT HEADER V21
    if not frappe.db.exists("HEADER V21", log.no_aju):
        h = frappe.new_doc("HEADER V21")
        h.nomoraju = log.no_aju
        h.kode_dokumen = (log.doctype_type or "").replace("BC", "")
        h.nama_entitas = header_data.get("namaEntitas") or "External Partner"
        h.nomor_daftar = log.nopen
        h.tanggal_daftar = log.nopen_date
        h.custom_is_external = 1
        h.insert(ignore_permissions=True)
    else:
        h = frappe.get_doc("HEADER V21", log.no_aju)
        h.nomor_daftar = log.nopen
        h.tanggal_daftar = log.nopen_date
        h.save(ignore_permissions=True)

    # 2. UPSERT BARANG
    for item in barang_data:
        seri = item.get("seriBarang") or item.get("seri")
        if not frappe.db.exists("BARANG", {"parent": h.name, "seri_barang": seri}):
            h.append("barang", {
                "seri_barang": seri,
                "kode_barang": item.get("kodeBarang"),
                "uraian": item.get("uraian"),
                "jumlah_satuan": flt(item.get("jumlahSatuan") or item.get("jumlah")),
                "kode_satuan": item.get("kodeSatuan"),
                "harga_satuan": flt(item.get("hargaSatuan") or item.get("harga"))
            })
    
    h.save(ignore_permissions=True)
    frappe.db.commit()
