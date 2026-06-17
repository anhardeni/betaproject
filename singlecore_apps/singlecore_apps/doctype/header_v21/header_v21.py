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


@frappe.whitelist()
def validate_manifest_and_kurs_endpoint(docname):
	doc = frappe.get_doc("HEADER V21", docname)
	doc._validate_and_sync_manifest_and_kurs()
	if doc.docstatus == 0:
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	return {"status": "success", "message": _("Validasi Manifest & Kurs berhasil dijalankan dan data diperbarui.")}


class HEADERV21(Document):
	def before_submit(self):
		self._validate_bahan_baku_dokumen_asal()
		self._validate_and_sync_manifest_and_kurs()

	def _validate_and_sync_manifest_and_kurs(self):
		# 1. Validasi & Sinkronisasi Kurs (Exchange Rate)
		valuta = self.kode_valuta
		if valuta and valuta != "IDR":
			from singlecore_apps.api.ceisa_api.kurs import get_kurs
			res = get_kurs(valuta)
			if res.get("status") == "success":
				data_ceisa = res.get("data", {})
				rows = data_ceisa.get("data", []) if isinstance(data_ceisa, dict) else []
				if rows and len(rows) > 0:
					nilai_kurs = rows[0].get("nilaiKurs")
					if nilai_kurs:
						self.ndpbm = float(nilai_kurs)
					else:
						frappe.throw(_("Gagal Validasi Kurs: Field 'nilaiKurs' tidak ditemukan dalam respon CEISA API."))
				else:
					frappe.throw(_("Gagal Validasi Kurs: Respon data kurs kosong untuk mata uang {0}.").format(valuta))
			else:
				frappe.throw(_("Gagal memanggil API Kurs CEISA: {0}").format(res.get("message")))
		elif valuta == "IDR":
			self.ndpbm = 1.0

		# 2. Validasi & Sinkronisasi Manifest (Hanya Dokumen Impor: 20, 23, 16)
		if self.kode_dokumen in ["20", "23", "16"]:
			# Ambil data BL / AWB dari child table dokumen
			no_host_bl = None
			tgl_host_bl = None
			for d in self.get("dokumen"):
				if d.kode_dokumen in ["705", "740", "704"]:
					no_host_bl = d.nomor_dokumen
					tgl_host_bl = d.tanggal_dokumen
					break

			if not no_host_bl or not tgl_host_bl:
				frappe.throw(_("Gagal Validasi: Dokumen pendukung Bill of Lading (705) atau Air Waybill (740) wajib diisi untuk dokumen impor."))

			# Ambil nama_perusahaan dari child table entitas (kode_entitas = 1 atau 5)
			nama_perusahaan = None
			for ent in self.get("entitas"):
				if ent.kode_entitas in ["1", "5"]:
					nama_perusahaan = ent.nama_entitas
					break

			if not nama_perusahaan:
				# Fallback ke nama company
				nama_perusahaan = frappe.db.get_value("Company", self.company, "company_name") or self.company

			if not nama_perusahaan:
				frappe.throw(_("Gagal Validasi Manifest: Nama Penerima / Importir tidak ditemukan pada entitas dokumen."))

			kode_kantor = self.kode_kantor
			if not kode_kantor:
				frappe.throw(_("Gagal Validasi Manifest: Kode Kantor wajib diisi."))

			from singlecore_apps.api.ceisa_api.manifes import get_manifes
			res_man = get_manifes(no_host_bl, tgl_host_bl, kode_kantor, nama_perusahaan)

			if res_man.get("status") == "success":
				data_man = res_man.get("data", {})
				man_item = None
				if isinstance(data_man, dict):
					inner_data = data_man.get("data")
					if isinstance(inner_data, list) and len(inner_data) > 0:
						man_item = inner_data[0]
					elif isinstance(inner_data, dict):
						man_item = inner_data
					else:
						man_item = data_man

				if not man_item or not (man_item.get("noBc11") or man_item.get("noPos")):
					frappe.throw(_("Manifest tidak ditemukan di CEISA untuk BL {0} dan Kantor {1}. Silakan periksa kembali kecocokan data Anda.").format(no_host_bl, kode_kantor))

				# Validasi Nama Importir
				ceisa_name = man_item.get("namaPenerima")
				if ceisa_name:
					def clean_name(n):
						import re
						s = str(n).lower()
						# Hapus singkatan badan usaha umum sebagai kata (boundaries)
						s = re.sub(r'\b(pt|cv|ud|tbk|persero|corp|co|ltd|gmbh)\b', '', s)
						# Hapus semua karakter non-alfanumerik
						s = re.sub(r'[^a-zA-Z0-9]', '', s)
						return s.strip()

					if clean_name(ceisa_name) != clean_name(nama_perusahaan):
						frappe.throw(_("Gagal Submit: Nama Penerima di Manifest CEISA ({0}) tidak cocok dengan Nama Importir di dokumen ({1}).").format(ceisa_name, nama_perusahaan))

				# Update field manifest
				self.nomor_bc11 = man_item.get("noBc11")
				self.tanggal_bc11 = man_item.get("tglBc11")
				self.nomor_pos = man_item.get("noPos")
				if man_item.get("noSubPos"):
					self.nomor_sub_pos = man_item.get("noSubPos")
			else:
				frappe.throw(_("Gagal memanggil API Manifest CEISA: {0}").format(res_man.get("message")))

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
