# Copyright (c) 2024, AnharDeni and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

def auto_create_customs_log(header_doc, payload_json, response_raw):
    """
    Fungsi Pemicu: Dipanggil saat dokumen berhasil terkirim ke server CEISA API (HTTP 200/201).
    Mencegah No Aju Ganda (Duplikasi) dengan logika Upsert.
    """
    import json
    try:
        p = json.loads(payload_json)
    except:
        p = {}

    no_aju = header_doc.get("nomoraju") or p.get("nomorAju") or p.get("nomor_aju")
    
    if not no_aju:
        frappe.log_error("Auto Create Log Gagal", "Nomor Aju tidak ditemukan di Doc maupun Payload")
        return

    # 1. Cek Cerdas (Anti Duplikasi & Revisi)
    if frappe.db.exists("Customs Status Log", no_aju):
        log = frappe.get_doc("Customs Status Log", no_aju)
        log.submission_datetime = now_datetime()
        log.payload_json = payload_json
        log.last_response_raw = response_raw
        
        # Bangunkan Robot Polling
        log.bc_status = "Pending"
        log.polling_interval = 5 # Reset ke 5 menit
        log.next_polling_time = now_datetime()
        
        log.save(ignore_permissions=True)
        return

    # 2. Pembuatan Dokumen Baru
    try:
        log = frappe.get_doc({
            "doctype": "Customs Status Log",
            "no_aju": no_aju,
            "doctype_type": header_doc.get("kode_dokumen"),
            "company": header_doc.get("company") or frappe.defaults.get_user_default("Company"),
            "linked_document_type": "HEADER V21",
            "linked_document_name": header_doc.name,
            "bc_status": "Pending",
            "submission_datetime": now_datetime(),
            "payload_json": payload_json,
            "last_response_raw": response_raw,
            "priority": "Medium",
            "polling_interval": 5,
            "next_polling_time": now_datetime()
        })
        log.insert(ignore_permissions=True)
        frappe.db.commit() # Pastikan tersimpan agar polling bisa jalan
        
    except Exception as e:
        frappe.log_error(f"Gagal Membuat Log BC Otomatis: {no_aju}", frappe.get_traceback())


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
