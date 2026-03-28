# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.utils import now_datetime, add_to_date

def smart_ceisa_polling():
    """Fungsi Penjadwal Otomatis (Anti-DDoS) berjalan via Frappe Scheduler"""
    
    # 1. Mencari log eksternal (PPJK/Subkon) yang statusnya belum selesai, 
    # dan waktu jadwal polling-nya (next_polling_time) sudah terlewati.
    pending_logs = frappe.get_all("Customs Status Log", 
        filters={
            "is_external_doc": 1,
            "bc_status": ["in", ["Pending", "Registered", "On Hold"]],
            "next_polling_time": ["<=", now_datetime()]
        }, 
        fields=["name", "no_aju", "kode_kantor", "polling_interval"]
    )

    # 2. Eksekusi penarikan data satu per satu
    for entry in pending_logs:
        success, message = trigger_sync_now(entry.name)
        frappe.logger("customs_sync").info(f"Sync Polling {entry.no_aju}: {message}")


@frappe.whitelist()
def trigger_sync_now(log_name):
    """
    Fungsi Penarik API Eksternal (API GET /document/detail).
    Bisa dipanggil manual via tombol UI (JS) atau dari fungsi smart_ceisa_polling di atas.
    """
    log = frappe.get_doc("Customs Status Log", log_name)
    
    no_aju = log.no_aju
    kode_kantor = log.kode_kantor
    doc_type = log.doctype_type
    
    # Validasi Dasar
    if not no_aju or not kode_kantor:
        return False, "Nomor Aju dan Kode Kantor Wajib Diisi untuk Dokumen Eksternal!"

    # -------------------------------------------------------------
    # 3. PANGGIL API CEISA
    # -------------------------------------------------------------
    # url = f"https://api.beacukai.go.id/document/detail/{doc_type}/{no_aju}/{kode_kantor}"
    # headers = {"Authorization": "Bearer ...", "beacukai-api-key": "..."}
    # response = requests.get(url, headers=headers)
    
    # SIMULASI response.json() dari API aslinya:
    api_response = {
        "status": "OK", # Anggap API membalas sukses
        "data": {
            "header": {
                "nomorAju": no_aju,
                "nomorDaftar": "REG-991122",
                "tanggalDaftar": "2026-03-25",
                "entitas_pemasok": "PT PEMASOK LUAR NEGERI"
            },
            "barang": [
                {"kodeBarang": "ITEM-01", "uraian": "Raw Material A", "jumlah": 150, "harga": 10}
            ]
        }
    }
    
    is_data_available = (api_response.get("status") == "OK")
    
    if is_data_available:
        try:
            # 4. DATA DITEMUKAN: Jalankan Fungsi Mapping ke Tabel Internal
            process_ceisa_detail_to_db(log, api_response["data"])
            
            # 5. Update Status Log menjadi Selesai agar polling terhenti
            log.bc_status = "Completed"
            log.polling_interval = 0
            log.next_polling_time = None 
            log.save(ignore_permissions=True)
            
            return True, "Berhasil Menarik Data Pabean Eksternal dari CEISA."
            
        except Exception as e:
            error_msg = f"Gagal Memproses Data JSON API: {str(e)}"
            frappe.log_error(title=f"Error Sync Eksternal {no_aju}", message=error_msg)
            return False, error_msg

    else:
        # 6. DATA BELUM ADA (PPJK BELUM SUBMIT): Jalankan Logika Smart Backoff
        interval = log.polling_interval or 1 # Default jeda 1 Jam
        
        # Tiap gagal, jeda ditambah 2 jam (Maksimal jeda penarikan adalah 24 jam)
        new_interval = interval + 2 
        if new_interval > 24:
            new_interval = 24 
            
        log.polling_interval = new_interval
        log.next_polling_time = add_to_date(now_datetime(), hours=new_interval)
        log.bc_status = "Pending"
        
        log.save(ignore_permissions=True)
        return False, f"Data CEISA Kosong. Reschedule ke: {log.next_polling_time}"


def process_ceisa_detail_to_db(log, data):
    """
    Memasukkan hasil JSON API CEISA ke dalam tabel internal (HEADER V21 & BARANG V1).
    Sehingga dokumen PPJK "menetas" (tercipta) di sistem ERP Anda secara otomatis.
    """
    no_aju = log.no_aju
    header_data = data.get("header", {})
    barang_data = data.get("barang", [])
    
    # Update Nomor Daftar di Log Utama (Jembatan Integrasi Laporan IT Inventory)
    log.nopen = header_data.get("nomorDaftar")
    log.nopen_date = header_data.get("tanggalDaftar")
    
    # 1. Buat Dokumen HEADER V21 (Hanya jika belum ada sebelumnya)
    if not frappe.db.exists("HEADER V21", no_aju):
        
        frappe.get_doc({
            "doctype": "HEADER V21",
            "nomoraju": no_aju,
            "kode_dokumen": log.doctype_type.replace("BC", ""),
            "nama_entitas": header_data.get("entitas_pemasok", "Nama Pemasok Eksternal"),
            "linked_purchase_order": log.linked_purchase_order, # Menyambungkan ke PO Gudang
            "custom_is_external": 1
        }).insert(ignore_permissions=True)
        
        # 2. Buat Detail BARANG V1
        for idx, item in enumerate(barang_data, start=1):
            frappe.get_doc({
                "doctype": "BARANG V1",
                "nomoraju": no_aju,
                "seri": idx,
                "kode_barang": item.get("kodeBarang"),
                "uraian": item.get("uraian"),
                "jumlah_satuan": item.get("jumlah"),
                "harga_satuan": item.get("harga")
            }).insert(ignore_permissions=True)
            
    # Commit perubahan struktur Database
    frappe.db.commit()
