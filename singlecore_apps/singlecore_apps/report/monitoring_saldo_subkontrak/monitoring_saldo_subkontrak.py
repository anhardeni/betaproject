# Copyright (c) 2026, Singlecore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, date_diff, today, getdate, format_date

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        { "label": _("Skenario"), "fieldname": "skenario", "fieldtype": "Data", "width": 120 },
        { "label": _("No. Aju Out"), "fieldname": "no_aju_keluar", "fieldtype": "Link", "options": "HEADER V21", "width": 200 },
        { "label": _("Tgl Daftar"), "fieldname": "tanggal_daftar", "fieldtype": "Date", "width": 100 },
        { "label": _("Nomor Kontrak"), "fieldname": "nomor_kontrak", "fieldtype": "Data", "width": 150 },
        { "label": _("Vendor/Penerima"), "fieldname": "entitas_penerima", "fieldtype": "Data", "width": 180 },
        { "label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Data", "width": 120 },
        { "label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180 },
        { "label": _("Qty Out"), "fieldname": "qty_keluar", "fieldtype": "Float", "width": 100 },
        { "label": _("Qty Retur/In"), "fieldname": "qty_masuk", "fieldtype": "Float", "width": 100 },
        { "label": _("Qty Sisa (BAL)"), "fieldname": "qty_outstanding", "fieldtype": "Float", "width": 120 },
        { "label": _("Jatuh Tempo"), "fieldname": "tgl_jatuh_tempo", "fieldtype": "Date", "width": 110 },
        { "label": _("Aging (Hari)"), "fieldname": "aging", "fieldtype": "Int", "width": 90 },
        { "label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100 }
    ]

def get_data(filters):
    data = []
    
    # 1. Bangun Query Filter untuk HEADER V21 (Dokumen Keluar)
    conditions = " 1=1 "
    if filters.get("from_date"):
        conditions += f" AND h.tanggal_daftar >= '{filters.get('from_date')}' "
    if filters.get("to_date"):
        conditions += f" AND h.tanggal_daftar <= '{filters.get('to_date')}' "
    if filters.get("vendor"):
        supplier_name = frappe.db.get_value("Supplier", filters.get("vendor"), "supplier_name") or filters.get("vendor")
        conditions += f" AND EXISTS (SELECT 1 FROM `tabENTITAS` WHERE parent = h.name AND kode_entitas = '4' AND nama_entitas = {frappe.db.escape(supplier_name)}) "
    
    # Ambil semua BC 261 dan BC 27 (Tujuan 4/Disubkon)
    # Kita join dengan ENTITAS untuk dapat nama penerima
    raw_query = f"""
        SELECT 
            h.name as header_id, h.nomoraju, h.tanggal_daftar, h.kode_dokumen,
            h.tgl_jatuh_tempo_subkon,
            (SELECT nama_entitas FROM `tabENTITAS` WHERE parent = h.name AND kode_entitas = '4' LIMIT 1) as entitas_penerima,
            b.kode_barang as item_code, b.uraian as item_name, b.jumlah_satuan as qty_keluar, b.seri_barang,
            (SELECT nomor_dokumen FROM `tabDOKUMEN` WHERE parent = h.name AND kode_dokumen = '315' LIMIT 1) as nomor_kontrak
        FROM `tabHEADER V21` h
        JOIN `tabBARANG` b ON b.parent = h.name
        WHERE {conditions}
        AND (
            h.kode_dokumen = '261' 
            OR (h.kode_dokumen = '27' AND h.kode_tujuan_pengeluaran = '4')
        )
        ORDER BY h.tanggal_daftar DESC, b.seri_barang ASC
    """
    
    outbound_docs = frappe.db.sql(raw_query, as_dict=1)

    for row in outbound_docs:
        # 2. Cek apakah sudah ada Rekonsiliasi untuk item ini (dengan agregasi SUM untuk partial return)
        recon_data = frappe.db.sql(f"""
            SELECT 
                SUM(ri.qty_masuk) as total_masuk, 
                SUM(ri.qty_scrap) as total_scrap,
                GROUP_CONCAT(r.status_rekon) as statuses
            FROM `tabSubcontract Reconciliation Item` ri
            JOIN `tabSubcontract Reconciliation` r ON r.name = ri.parent
            WHERE r.header_keluar = '{row.header_id}' 
            AND ri.item_code = '{row.item_code}'
            AND r.docstatus = 1
        """, as_dict=1)

        qty_masuk = 0
        qty_scrap = 0
        
        if recon_data and recon_data[0].get("total_masuk") is not None:
            qty_masuk = flt(recon_data[0].total_masuk)
            qty_scrap = flt(recon_data[0].total_scrap)
            
        total_returned = qty_masuk + qty_scrap
        qty_outstanding = flt(row.qty_keluar) - total_returned
        status_label = "Outstanding"
        
        if qty_outstanding <= 0:
            status_label = "Settled"
        else:
            if recon_data and recon_data[0].get("statuses"):
                states = [s.strip() for s in recon_data[0].statuses.split(",") if s]
                if "Under Reconciliation" in states:
                    status_label = "Under Reconciliation"
        
        # 3. Hitung Aging (Sisa Hari)
        aging = 0
        jatuh_tempo = row.tgl_jatuh_tempo_subkon
        if jatuh_tempo:
            aging = date_diff(getdate(jatuh_tempo), getdate(today()))

        # 4. Terapkan Filter Status (Pilihan User di UI)
        if filters.get("status"):
            if filters.get("status") == "Outstanding" and qty_outstanding <= 0:
                continue
            if filters.get("status") == "Settled" and qty_outstanding > 0:
                continue

        # 5. Terapkan Filter Skenario
        skenario_label = "BC 261" if row.kode_dokumen == "261" else "BC 27"
        if filters.get("skenario"):
            if "261" in filters.get("skenario") and row.kode_dokumen != "261":
                continue
            if "27" in filters.get("skenario") and row.kode_dokumen != "27":
                continue

        data.append({
            "skenario": skenario_label,
            "no_aju_keluar": row.header_id,
            "tanggal_daftar": row.tanggal_daftar,
            "nomor_kontrak": row.nomor_kontrak,
            "entitas_penerima": row.entitas_penerima,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "qty_keluar": row.qty_keluar,
            "qty_masuk": qty_masuk + qty_scrap,
            "qty_outstanding": qty_outstanding,
            "tgl_jatuh_tempo": jatuh_tempo,
            "aging": aging,
            "status": status_label
        })

    return data

