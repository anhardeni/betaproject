# Copyright (c) 2026, Singlecore and contributors
# For license information, please see license.txt
"""
Subcontract Reconciliation
===========================
Modul untuk merekonsiliasi saldo barang subkontrak antara:
  - Skenario A: BC 2.6.1 (Keluar) vs BC 2.6.2 (Masuk) → Subkontrak Umum
  - Skenario B: BC 2.7 (Keluar) vs BC 2.7 (Masuk)    → Subkontrak Antar KB

Setiap baris material memiliki:
  qty_keluar → qty_masuk + qty_scrap = saldo (qty_outstanding)

Status Rekonsiliasi:
  Outstanding        → belum ada retur sama sekali
  Partially Settled  → ada retur, tapi qty_outstanding > 0
  Settled            → qty_outstanding semua baris = 0
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SubcontractReconciliation(Document):

    # ─── Before Save ─────────────────────────────────────────────────────────
    def before_save(self):
        self._set_skenario_kode()
        self._calculate_items()
        self._calculate_totals()
        self._set_status()

    def before_submit(self):
        self._validate_before_submit()
        self._calculate_items()
        self._calculate_totals()
        self._set_status()

    def on_submit(self):
        """Setelah disubmit: update flag di HEADER V21 Keluar jika Settled."""
        if self.status_rekon == "Settled":
            self._flag_header_as_settled()

    def on_cancel(self):
        """Batalkan flag Settled di HEADER V21 jika rekon dibatalkan."""
        self._unflag_header_settled()

    # ─── Logika Inti ─────────────────────────────────────────────────────────
    def _set_skenario_kode(self):
        """Tentukan kode pendek untuk naming series."""
        if self.skenario and "261" in self.skenario:
            self.skenario_kode = "261"
        else:
            self.skenario_kode = "27"

    def _calculate_items(self):
        """Hitung qty_outstanding per baris: keluar - masuk - scrap."""
        for row in self.items:
            keluar = flt(row.qty_keluar, 4)
            masuk = flt(row.qty_masuk, 4)
            scrap = flt(row.qty_scrap, 4)
            row.qty_outstanding = max(keluar - masuk - scrap, 0)

    def _calculate_totals(self):
        """Hitung total kolom dan persentase selesai."""
        self.total_qty_keluar    = sum(flt(r.qty_keluar, 4) for r in self.items)
        self.total_qty_masuk     = sum(flt(r.qty_masuk, 4) for r in self.items)
        self.total_qty_scrap     = sum(flt(r.qty_scrap, 4) for r in self.items)
        self.total_qty_outstanding = sum(flt(r.qty_outstanding, 4) for r in self.items)

        if self.total_qty_keluar > 0:
            settled = self.total_qty_keluar - self.total_qty_outstanding
            self.persentase_selesai = round((settled / self.total_qty_keluar) * 100, 2)
        else:
            self.persentase_selesai = 0

    def _set_status(self):
        """Tentukan status rekonsiliasi berdasarkan outstanding."""
        if not self.items:
            self.status_rekon = "Outstanding"
            return

        all_zero = all(flt(r.qty_outstanding) == 0 for r in self.items)
        any_returned = any(flt(r.qty_masuk) + flt(r.qty_scrap) > 0 for r in self.items)

        if all_zero and any_returned:
            self.status_rekon = "Settled"
        elif any_returned:
            self.status_rekon = "Partially Settled"
        else:
            self.status_rekon = "Outstanding"

    def _validate_before_submit(self):
        """Validasi kelengkapan sebelum submit."""
        if not self.items:
            frappe.throw(_("Rincian barang tidak boleh kosong sebelum di-submit."))
        if not self.header_keluar:
            frappe.throw(_("HEADER V21 Keluar wajib diisi."))
        for i, row in enumerate(self.items, 1):
            if flt(row.qty_keluar) <= 0:
                frappe.throw(_(f"Baris {i}: Qty Keluar harus lebih dari 0."))

    # ─── Flagging HEADER V21 ─────────────────────────────────────────────────
    def _flag_header_as_settled(self):
        """Tandai HEADER V21 keluar sebagai Settled (field subkon_settled)."""
        try:
            # Cek apakah field ada (future-proof)
            meta = frappe.get_meta("HEADER V21")
            if meta.has_field("subkon_settled"):
                frappe.db.set_value(
                    "HEADER V21", self.header_keluar,
                    "subkon_settled", 1
                )
            # Tambahkan komentar di dokumen sumber
            doc = frappe.get_doc("HEADER V21", self.header_keluar)
            doc.add_comment(
                "Comment",
                f"✅ Subkontrak SETTLED via Rekonsiliasi: {self.name} pada {frappe.utils.today()}"
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Subcon: Gagal flag HEADER V21 settled")

    def _unflag_header_settled(self):
        """Hapus flag Settled dari HEADER V21 jika rekon dibatalkan."""
        try:
            meta = frappe.get_meta("HEADER V21")
            if meta.has_field("subkon_settled"):
                frappe.db.set_value(
                    "HEADER V21", self.header_keluar,
                    "subkon_settled", 0
                )
            doc = frappe.get_doc("HEADER V21", self.header_keluar)
            doc.add_comment(
                "Comment",
                f"🔄 Status Settled DIBATALKAN — Rekonsiliasi {self.name} di-cancel."
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Subcon: Gagal unflag HEADER V21")


# ─── API: Tarik Item dari HEADER V21 Keluar ──────────────────────────────────
@frappe.whitelist()
def get_items_from_header(header_name):
    """
    Tarik daftar barang dari child table BARANG di HEADER V21.
    Dipanggil Client Script saat user memilih header_keluar.
    """
    try:
        if not frappe.db.exists("HEADER V21", header_name):
            frappe.throw(_(f"HEADER V21 '{header_name}' tidak ditemukan."))

        # Ambil dari child table BARANG (nama child table sesuai DocType Anda)
        # Ambil dari child table BARANG di HEADER V21
        # field nyata: kode_barang, uraian, kode_satuan, jumlah_satuan
        items = frappe.get_all(
            "BARANG",
            filters={"parent": header_name, "parenttype": "HEADER V21"},
            fields=["kode_barang", "uraian", "kode_satuan", "jumlah_satuan", "seri_barang"],
            order_by="seri_barang asc"
        )

        result = []
        for item in items:
            qty = flt(item.get("jumlah_satuan"), 4)
            result.append({
                "item_code": item.get("kode_barang") or item.get("hs"),
                "item_name": item.get("uraian"),
                "satuan": item.get("kode_satuan"),
                "qty_keluar": qty,
                "qty_masuk": 0,
                "qty_scrap": 0,
                "qty_outstanding": qty
            })

        return result

    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_items_from_header Error")
        return []
