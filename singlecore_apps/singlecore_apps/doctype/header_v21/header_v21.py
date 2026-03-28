# Copyright (c) 2024, AnharDeni and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

def auto_create_customs_log(header_doc, payload_json, response_raw):
    """
    Fungsi Pemicu: Dipanggil saat dokumen berhasil terkirim ke server CEISA API (HTTP 200).
    Mencegah No Aju Ganda (Duplikasi) dengan logika Upsert.
    """
    no_aju = header_doc.nomoraju
    
    if not no_aju:
        frappe.log_error("Auto Create Log Gagal", "Nomor Aju Kosong pada HEADER V21")
        return

    # 1. Cek Cerdas (Anti Duplikasi & Revisi)
    if frappe.db.exists("Customs Status Log", no_aju):
        # Jika dokumen log aslinya sudah ada, kita hanya "menimpa" update terbarunya
        # dan membangunkan robot polling lagi agar mencari status barunya ke CEISA.
        log = frappe.get_doc("Customs Status Log", no_aju)
        log.submission_datetime = now_datetime()
        log.payload_json = payload_json
        log.last_response_raw = response_raw
        
        # Bangunkan Robot Polling
        log.bc_status = "Pending"
        log.polling_interval = 1
        log.next_polling_time = now_datetime()
        
        log.save(ignore_permissions=True)
        frappe.logger("customs_integration").info(f"Log BC Updated (Revisi) untuk Aju: {no_aju}")
        return

    # 2. Pembuatan Dokumen Baru
    try:
        log = frappe.get_doc({
            "doctype": "Customs Status Log",
            "no_aju": no_aju,
            "doctype_type": header_doc.kode_dokumen, # Pastikan formatnya "BC23" dll
            "company": frappe.defaults.get_user_default("Company") or "Nama Perusahaan Anda",
            
            # Tali Pusar ke Dokumen Induk (Traceability Audit)
            "linked_document_type": "HEADER V21",
            "linked_document_name": header_doc.name,
            
            # Status Awal
            "bc_status": "Pending",
            "submission_datetime": now_datetime(),
            "payload_json": payload_json,
            "last_response_raw": response_raw,
            
            # Jadwal Robot Polling Pertama Kali
            "priority": "Medium",
            "polling_interval": 1,
            "next_polling_time": now_datetime()
        })
        log.insert(ignore_permissions=True)
        frappe.logger("customs_integration").info(f"Log BC Baru Diciptakan untuk Aju: {no_aju}")
        
    except Exception as e:
        frappe.log_error(f"Gagal Membuat Log BC Otomatis: {no_aju}", str(e))


class HEADERV21(Document):
	def on_cancel(self):
		"""Mematikan jadwal pencarian robot saat dokumen dibatalkan"""
		no_aju = self.nomoraju
		if no_aju and frappe.db.exists("Customs Status Log", no_aju):
			frappe.db.set_value("Customs Status Log", no_aju, "bc_status", "Cancelled")
			frappe.db.set_value("Customs Status Log", no_aju, "next_polling_time", None)

	def on_trash(self):
		"""Mematikan jadwal pencarian robot saat dokumen dihapus fisik"""
		no_aju = self.nomoraju
		if no_aju and frappe.db.exists("Customs Status Log", no_aju):
			frappe.db.set_value("Customs Status Log", no_aju, "bc_status", "Cancelled")
			frappe.db.set_value("Customs Status Log", no_aju, "next_polling_time", None)
