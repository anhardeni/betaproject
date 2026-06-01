# Copyright (c) 2024, AnharDeni and contributors
# For license information, please see license.txt
import frappe
from frappe import _
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
            "linked_document_name": header_doc.name if frappe.db.exists("HEADER V21", header_doc.name) else None,
            "bc_status": "Pending",
            "submission_datetime": now_datetime(),
            "payload_json": payload_json,
            "last_response_raw": response_raw,
            "priority": "Medium",
            "polling_interval": 5,
            "next_polling_time": now_datetime()
        })
        log.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit() # Pastikan tersimpan agar polling bisa jalan
        
    except Exception as e:
        frappe.log_error(f"Gagal Membuat Log BC Otomatis: {no_aju}", frappe.get_traceback())


class HEADERV21(Document):
	def before_submit(self):
		self._validate_bahan_baku_dokumen_asal()

	def _validate_bahan_baku_dokumen_asal(self):
		"""
		Opsi C (Hibrida): Memastikan seluruh bahan baku pabean untuk dokumen pengeluaran
		(BC 2.5, BC 2.7, BC 2.6.1) memiliki dokumen asal pabean yang lengkap sebelum di-submit.
		"""
		if self.kode_dokumen not in ("25", "27", "261"):
			return

		# Ambil seluruh bahan baku yang berasosiasi dengan barang di header ini
		sql = """
			SELECT
				bb.name, bb.kode_barang, bb.seri_barang, bb.seri_bahan_baku, bb.nomor_aju_asal
			FROM
				`tabBAHAN BAKU` bb
				INNER JOIN `tabBARANG V1` b ON b.name = bb.parent_barang
			WHERE
				b.nomoraju = %(header_name)s
		"""
		raw_materials = frappe.db.sql(sql, {"header_name": self.name}, as_dict=True)

		if not raw_materials:
			return

		unallocated = []
		for rm in raw_materials:
			if not rm.nomor_aju_asal or rm.nomor_aju_asal.strip() == "" or "TIDAK CUKUP" in str(rm.nomor_aju_asal).upper():
				unallocated.append(f"- Seri {rm.seri_barang} Bahan Baku {rm.kode_barang} (Seri BB {rm.seri_bahan_baku})")

		if unallocated:
			msg = _("<b>Gagal Submit: Kepatuhan Dokumen Asal Pabean (Opsi C)</b><br>"
					"Ditemukan bahan baku hasil konversi BOM yang belum teralokasi dokumen asal masuknya (BC 2.3 / BC 4.0 / BC 2.7 Masuk). "
					"Silakan lengkapi dokumen asal secara manual atau sinkronkan data pabean masuk Anda:<br><br>")
			msg += "<br>".join(unallocated[:10])
			if len(unallocated) > 10:
				msg += f"<br>...dan {len(unallocated) - 10} item lainnya."
			frappe.throw(msg, title=_("Stok Pabean Kurang"))

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
