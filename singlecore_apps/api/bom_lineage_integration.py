# -*- coding: utf-8 -*-
# Copyright (c) 2026, AnharDeni and contributors
# License: MIT

"""
BOM & FIFO Lineage Integration
==============================
Mengotomatisasi konversi Barang Jadi (Finished Goods) ke Bahan Baku menggunakan BOM,
serta melacak dokumen pabean asal pemasukan (BC 2.3, BC 4.0, BC 2.7 Masuk) secara FIFO.
Mengimplementasikan Opsi C (Hibrida): draft diizinkan, submit diblokir jika saldo kurang.
"""

import frappe
from frappe import _
from frappe.utils import flt, today, getdate

# ═══════════════════════════════════════════════════════════════════
# 1. GET RAW MATERIALS FROM BOM (SINGLE-LEVEL)
# ═══════════════════════════════════════════════════════════════════

def get_bom_materials(item_code, target_qty):
    """
    Mengambil rincian bahan baku dari BOM aktif untuk Finished Goods (item_code)
    dan mengalikan kuantitas kebutuhan dengan target_qty barang jadi.
    
    Returns:
        List of dict berisi informasi item bahan baku.
    """
    # Cari BOM aktif di sistem
    bom_name = frappe.db.get_value("Item", item_code, "default_bom")
    if not bom_name:
        bom_name = frappe.db.get_value(
            "BOM", 
            {"item": item_code, "is_active": 1, "docstatus": 1}, 
            "name", 
            order_by="creation desc"
        )
        
    if not bom_name:
        return []
        
    bom = frappe.get_doc("BOM", bom_name)
    bom_qty = flt(bom.quantity) or 1.0
    
    materials = []
    for item in bom.items:
        # Rumus Kebutuhan: (Qty BOM Item / Qty Parent BOM) * Target Qty FG
        required_qty = (flt(item.qty) / bom_qty) * flt(target_qty)
        
        materials.append({
            "kode_barang": item.item_code,
            "uraian": item.item_name or item.item_code,
            "jumlah_satuan": flt(required_qty, 4),
            "uom": item.uom,
            "harga_satuan": flt(item.rate, 4),
            "cif": flt(item.rate, 4) * required_qty
        })
        
    return materials


# ═══════════════════════════════════════════════════════════════════
# 2. FIFO INVENTORY TRACING FOR CUSTOMS DOCUMENTS
# ═══════════════════════════════════════════════════════════════════

def get_available_inbound_stock(item_code):
    """
    Mencari seluruh baris barang masuk pabean (BC 2.3, BC 4.0, BC 2.7 Masuk)
    untuk item tertentu yang masih memiliki saldo pabean belum terpakai.
    Diurutkan secara FIFO berdasarkan tanggal pendaftaran dokumen pabean masuk.
    """
    # Query untuk mengambil seluruh baris BARANG V1 dari dokumen masuk (docstatus=1)
    # Join ke Customs Status Log untuk mengambil nopen & nopen_date (No/Tgl Daftar Asli)
    sql_inbound = """
        SELECT
            b.name AS barang_v1_name,
            b.nomoraju AS nomoraju_parent,
            h.nomoraju AS nomor_aju,
            b.seri_barang AS seri_barang,
            h.kode_dokumen AS kode_dokumen,
            h.kode_kantor AS kode_kantor,
            csl.nopen AS nomor_daftar,
            COALESCE(csl.nopen_date, h.tanggal_pernyataan) AS tanggal_daftar,
            b.jumlah_satuan AS original_qty,
            b.hs AS hs_code,
            b.merek AS merek,
            b.tipe AS tipe,
            b.ukuran AS ukuran,
            b.spesifikasi_lain AS spesifikasi_lain,
            b.kode_satuan AS kode_satuan,
            b.kode_asal_barang AS kode_asal_barang
        FROM
            `tabBARANG V1` b
            INNER JOIN `tabHEADER V21` h ON h.name = b.nomoraju
            LEFT JOIN `tabCustoms Status Log` csl ON csl.no_aju = h.nomoraju
        WHERE
            b.kode_barang = %(item_code)s
            AND h.kode_dokumen IN ('23', '40', '27')
            AND (csl.nopen IS NOT NULL OR h.docstatus = 1)
        ORDER BY
            COALESCE(csl.nopen_date, h.tanggal_pernyataan) ASC,
            h.creation ASC
    """
    
    inbound_items = frappe.db.sql(sql_inbound, {"item_code": item_code}, as_dict=True)
    available_queue = []
    
    for item in inbound_items:
        # Hitung kuantitas yang sudah dikonsumsi oleh dokumen BAHAN BAKU lain
        # yang parent-nya (Finished Goods / BARANG V1) aktif (tidak di-cancel)
        sql_consumed = """
            SELECT
                SUM(bb.jumlah_satuan) AS consumed
            FROM
                `tabBAHAN BAKU` bb
                INNER JOIN `tabBARANG V1` parent_fg ON parent_fg.name = bb.parent_barang
                INNER JOIN `tabHEADER V21` parent_h ON parent_h.name = parent_fg.nomoraju
            WHERE
                bb.nomor_aju_asal = %(nomor_aju)s
                AND bb.seri_barang_asal = %(seri_barang)s
                AND parent_h.docstatus != 2
        """
        
        res = frappe.db.sql(sql_consumed, {
            "nomor_aju": item.nomor_aju,
            "seri_barang": item.seri_barang
        }, as_dict=True)
        
        consumed_qty = flt(res[0].consumed) if res and res[0].consumed else 0.0
        remaining_qty = flt(item.original_qty) - consumed_qty
        
        if remaining_qty > 0.0001:
            item["available_qty"] = remaining_qty
            available_queue.append(item)
            
    return available_queue


def allocate_fifo_materials(item_code, required_qty):
    """
    Mengalokasikan kebutuhan bahan baku dari antrean FIFO dokumen masuk.
    Jika stok pabean tidak cukup (Opsi C):
        Sisa alokasi akan ditandai kosong agar diisi/rekon manual nanti.
        
    Returns:
        List of dict berisi alokasi per dokumen asal pabean.
    """
    queue = get_available_inbound_stock(item_code)
    allocations = []
    remaining_to_allocate = flt(required_qty, 4)
    
    for inbound_item in queue:
        if remaining_to_allocate <= 0:
            break
            
        take = min(inbound_item["available_qty"], remaining_to_allocate)
        
        allocations.append({
            "is_allocated": True,
            "jumlah_satuan": flt(take, 4),
            "kode_dokumen_asal": inbound_item["kode_dokumen"],
            "kode_kantor_asal": inbound_item["kode_kantor"],
            "nomor_daftar_asal": inbound_item["nomor_daftar"] or "BELUM DAFTAR",
            "tanggal_daftar_asal": inbound_item["tanggal_daftar"],
            "nomor_aju_asal": inbound_item["nomor_aju"],
            "seri_barang_asal": inbound_item["seri_barang"],
            "kode_asal_bahan_baku": inbound_item["kode_asal_barang"] or "1", # 0=Impor, 1=Lokal
            "hs": inbound_item["hs_code"],
            "merek": inbound_item["merek"],
            "tipe": inbound_item["tipe"],
            "ukuran": inbound_item["ukuran"],
            "spesifikasi_lain": inbound_item["spesifikasi_lain"]
        })
        
        remaining_to_allocate = flt(remaining_to_allocate - take, 4)
        
    # Jika stok kurang (Opsi C: Izinkan Draft kosong / menggantung)
    if remaining_to_allocate > 0.0001:
        # Cari data item master untuk kelengkapan info dasar
        item_meta = frappe.db.get_value("Item", item_code, ["item_name", "customs_tariff_number", "brand"], as_dict=True) or {}
        allocations.append({
            "is_allocated": False, # Flag penanda tidak teralokasi pabean (Merah/Kuning di UI)
            "jumlah_satuan": flt(remaining_to_allocate, 4),
            "kode_dokumen_asal": "",
            "kode_kantor_asal": "",
            "nomor_daftar_asal": "STOK PABEAN TIDAK CUKUP",
            "tanggal_daftar_asal": None,
            "nomor_aju_asal": "",
            "seri_barang_asal": 0,
            "kode_asal_bahan_baku": "1", # Default lokal
            "hs": item_meta.get("customs_tariff_number") or "",
            "merek": item_meta.get("brand") or "",
            "tipe": "",
            "ukuran": "",
            "spesifikasi_lain": "PERINGATAN: Sisa stok pabean tidak mencukupi untuk baris ini."
        })
        
    return allocations


# ═══════════════════════════════════════════════════════════════════
# 3. MAIN SERVICE: POPULATE RAW MATERIALS TO DOKUMEN (HEADER V21)
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def populate_raw_materials_from_bom(header_name):
    """
    Dipanggil saat HEADER V21 dibuat dari SO/SI/DN.
    Fungsi ini akan menghapus data BAHAN BAKU lama untuk header ini,
    lalu menarik data Finished Goods dari BARANG V1, melakukan konversi BOM,
    menjalankan FIFO, dan mengisi tabel BAHAN BAKU.
    """
    if not frappe.db.exists("HEADER V21", header_name):
        return {"status": "error", "message": f"HEADER V21 {header_name} tidak ditemukan."}
        
    header = frappe.get_doc("HEADER V21", header_name)
    
    # Hanya jalankan untuk dokumen keluaran/produksi: BC 2.5, BC 2.7, BC 2.6.1
    if header.kode_dokumen not in ("25", "27", "261"):
        return {"status": "success", "message": f"Dokumen BC{header.kode_dokumen} tidak memerlukan konversi bahan baku."}
        
    try:
        # 1. Hapus record BAHAN BAKU lama yang berasosiasi dengan BARANG V1 milik header ini
        # Ambil seluruh BARANG V1 milik header ini
        barang_fg = frappe.get_all("BARANG V1", filters={"nomoraju": header_name}, fields=["name", "kode_barang", "jumlah_satuan", "seri_barang"])
        
        for fg in barang_fg:
            frappe.db.delete("BAHAN BAKU", {"parent_barang": fg.name})
            
        # 2. Proses Konversi BOM & FIFO per Finished Goods
        total_bahan_baku_added = 0
        warnings = []
        
        for fg in barang_fg:
            raw_materials = get_bom_materials(fg.kode_barang, fg.jumlah_satuan)
            
            if not raw_materials:
                warnings.append(f"FG {fg.kode_barang} (Seri {fg.seri_barang}) tidak memiliki BOM aktif di ERPNext.")
                continue
                
            seri_bahan_baku = 1
            for rm in raw_materials:
                # Alokasikan dokumen asal secara FIFO
                allocations = allocate_fifo_materials(rm["kode_barang"], rm["jumlah_satuan"])
                
                for alloc in allocations:
                    # Buat record BAHAN BAKU baru
                    bb = frappe.new_doc("BAHAN BAKU")
                    bb.parent_barang = fg.name
                    bb.nomoraju = header_name
                    bb.seri_barang = fg.seri_barang
                    bb.seri_bahan_baku = seri_bahan_baku
                    
                    bb.kode_barang = rm["kode_barang"]
                    bb.uraian = rm["uraian"]
                    bb.jumlah_satuan = alloc["jumlah_satuan"]
                    bb.kode_satuan = rm["uom"]
                    
                    # Salin atribut alokasi pabean masuk
                    bb.kode_dokumen_asal = alloc["kode_dokumen_asal"]
                    bb.kode_kantor_asal = alloc["kode_kantor_asal"]
                    bb.nomor_daftar_asal = alloc["nomor_daftar_asal"]
                    bb.tanggal_daftar_asal = alloc["tanggal_daftar_asal"]
                    bb.nomor_aju_asal = alloc["nomor_aju_asal"]
                    bb.seri_barang_asal = alloc["seri_barang_asal"]
                    bb.kode_asal_bahan_baku = alloc["kode_asal_bahan_baku"]
                    
                    bb.hs = alloc["hs"] or rm.get("hs") or ""
                    bb.merek = alloc["merek"] or rm.get("merek") or ""
                    bb.tipe = alloc["tipe"] or ""
                    bb.ukuran = alloc["ukuran"] or ""
                    bb.spesifikasi_lain = alloc["spesifikasi_lain"]
                    
                    # Kalkulasi berat / finansial pabean dasar
                    item_weight = flt(frappe.db.get_value("Item", rm["kode_barang"], "weight_per_unit")) or 1.0
                    bb.netto = flt(alloc["jumlah_satuan"] * item_weight, 4)
                    bb.bruto = flt(bb.netto * 1.05, 4)
                    
                    # Tentukan CIF / FOB (untuk bahan baku proporsional rate)
                    bb.harga_perolehan = flt(rm["harga_satuan"], 4)
                    bb.harga_penyerahan = flt(rm["harga_satuan"], 4)
                    
                    # REGULASI KAWASAN BERIKAT: Kandungan Lokal (BC 4.0 atau Asal Lokal)
                    # Bea Masuk dan PDRI hanya dikenakan pada proporsi bahan baku impor (BC 2.3).
                    # Maka atas asal BC 4.0 atau lokal, nilai CIF & CIF RUPIAH diset ke 0.
                    if alloc["kode_dokumen_asal"] == "40" or alloc["kode_asal_bahan_baku"] == "1":
                        bb.cif = 0.0
                        bb.cif_rupiah = 0.0
                    else:
                        bb.cif = flt(rm["harga_satuan"] * alloc["jumlah_satuan"], 2)
                        ndpbm = flt(header.get("ndpbm") or 1.0)
                        bb.cif_rupiah = flt(bb.cif * ndpbm, 2)
                    
                    # Tambahkan flag khusus warning di spesifikasi jika tidak teralokasi
                    if not alloc["is_allocated"]:
                        bb.spesifikasi_lain = "⚠️ [UNALLOCATED] " + bb.spesifikasi_lain
                        warnings.append(f"Bahan Baku {rm['kode_barang']} kekurangan stok pabean masuk sebesar {alloc['jumlah_satuan']} satuan.")
                        
                    bb.insert(ignore_permissions=True)
                    seri_bahan_baku += 1
                    total_bahan_baku_added += 1
                    
        frappe.db.commit()
        
        # Susun laporan umpan balik
        status = "success"
        message = f"Berhasil mengonversi BOM dan menambahkan {total_bahan_baku_added} entri bahan baku pabean."
        if warnings:
            message += "<br><br><strong>⚠️ Peringatan Integrasi:</strong><br>" + "<br>".join(warnings[:8])
            if len(warnings) > 8:
                message += f"<br>...dan {len(warnings) - 8} peringatan lainnya."
                
        return {
            "status": status,
            "message": message,
            "total_added": total_bahan_baku_added,
            "warnings": warnings
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Populate Raw Materials BOM FIFO Error")
        return {"status": "error", "message": f"Terjadi kesalahan saat memproses konversi BOM: {str(e)}"}
