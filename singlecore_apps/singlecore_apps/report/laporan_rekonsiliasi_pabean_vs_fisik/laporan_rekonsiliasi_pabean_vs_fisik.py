# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data

def get_columns():
    return [
        {"label": _("Tipe BC"),           "fieldname": "bc_type",         "fieldtype": "Data",         "width": 80},
        {"label": _("No. Daftar BC"),     "fieldname": "bc_reg_no",       "fieldtype": "Data",         "width": 140},
        {"label": _("Tgl. Daftar BC"),    "fieldname": "bc_reg_date",     "fieldtype": "Date",         "width": 110},
        {"label": _("Item Code"),         "fieldname": "item_code",       "fieldtype": "Link",         "width": 130, "options": "Item"},
        {"label": _("Nama Barang"),       "fieldname": "item_name",       "fieldtype": "Data",         "width": 180},
        {"label": _("Qty (Pabean)"),      "fieldname": "qty_bc",          "fieldtype": "Float",        "width": 110},
        {"label": _("Qty (ERP Fisik)"),   "fieldname": "qty_fisik",       "fieldtype": "Float",        "width": 110},
        {"label": _("Selisih"),           "fieldname": "selisih",         "fieldtype": "Float",        "width": 110},
        {"label": _("Status"),            "fieldname": "status",          "fieldtype": "Data",         "width": 120},
        {"label": _("Ref Transaksi"),      "fieldname": "ref_docs",        "fieldtype": "Data",         "width": 200},
    ]

def get_data(filters):
    # 1. Get Pabean Data (Header V21 + Barang V1)
    pabean_data = get_pabean_data(filters)
    
    # 2. Get Physical Data (PR, DN, SE)
    physical_summary = get_physical_summary(filters)
    
    data = []
    
    # Track which physical docs were matched to mark "Missing Pabean" if needed 
    # (though usually Pabean is the lead record in this report)
    
    for key, p in pabean_data.items():
        qty_bc = p["qty"]
        phys = physical_summary.get(key, {"qty": 0, "docs": []})
        qty_fisik = phys["qty"]
        selisih = qty_bc - qty_fisik
        
        status = "Matched"
        if selisih > 0:
            status = "Under-delivered" if qty_fisik > 0 else "Pending Receipt/Issue"
        elif selisih < 0:
            status = "Over-delivered"
            
        data.append({
            "bc_type": p["bc_type"],
            "bc_reg_no": p["bc_no"],
            "bc_reg_date": p["bc_date"],
            "item_code": p["item_code"],
            "item_name": p["item_name"],
            "qty_bc": qty_bc,
            "qty_fisik": qty_fisik,
            "selisih": selisih,
            "status": status,
            "ref_docs": ", ".join(phys["docs"]) if phys["docs"] else "-"
        })
    
    # Optional: Find Physical transactions that HAVE BC identifiers but NO matching Header V21
    for key, phys in physical_summary.items():
        if key not in pabean_data:
            data.append({
                "bc_type": key[0],
                "bc_reg_no": key[1],
                "bc_reg_date": None,
                "item_code": key[2],
                "item_name": "Unknown (No CEISA Doc Found)",
                "qty_bc": 0,
                "qty_fisik": phys["qty"],
                "selisih": -phys["qty"],
                "status": "Missing Pabean Doc",
                "ref_docs": ", ".join(phys["docs"])
            })

    return data

def get_pabean_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    bc_type_f = filters.get("bc_type")
    
    cond = "h.docstatus = 1"
    params = {}
    if from_date:
        cond += " AND h.tanggal_daftar >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        cond += " AND h.tanggal_daftar <= %(to_date)s"
        params["to_date"] = to_date
    if bc_type_f:
        # Filter is 'BC23', database is '23'
        params["bc_kode"] = bc_type_f.replace("BC", "")
        cond += " AND h.kode_dokumen = %(bc_kode)s"
        
    sql = f"""
        SELECT 
            h.kode_dokumen as bc_kode,
            h.nomor_daftar as bc_no,
            h.tanggal_daftar as bc_date,
            b.kode_barang as item_code,
            b.uraian as item_name,
            SUM(b.jumlah_satuan) as qty
        FROM `tabHEADER V21` h
        INNER JOIN `tabBARANG V1` b ON b.nomoraju = h.name
        WHERE {cond}
        GROUP BY h.kode_dokumen, h.nomor_daftar, b.kode_barang
    """
    res = frappe.db.sql(sql, params, as_dict=True)
    summary = {}
    for r in res:
        # Normalize bc_type to 'BCXX' for matching
        bc_type = f"BC{r.bc_kode}"
        key = (bc_type, r.bc_no, r.item_code)
        summary[key] = {
            "bc_type": bc_type,
            "bc_no": r.bc_no,
            "bc_date": r.bc_date,
            "item_code": r.item_code,
            "item_name": r.item_name,
            "qty": flt(r.qty)
        }
    return summary

def get_physical_summary(filters):
    bc_type_f = filters.get("bc_type")
    
    # We query PR, DN, and SE
    summary = {}

    def add_to_summary(rows):
        for r in rows:
            if not r.bc_no: continue
            key = (r.bc_type, r.bc_no, r.item_code)
            if key not in summary:
                summary[key] = {"qty": 0, "docs": set()}
            summary[key]["qty"] += flt(r.qty)
            summary[key]["docs"].add(r.parent)

    # PR
    pr_rows = frappe.db.sql(f"""
        SELECT 
            pri.parent, 
            pr.custom_bc_document_type as bc_type, 
            pr.custom_bc_registration_no as bc_no, 
            pri.item_code, 
            pri.qty
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE pr.docstatus = 1 {'AND pr.custom_bc_document_type = %(bc)s' if bc_type_f else ''}
    """, {"bc": bc_type_f}, as_dict=True)
    add_to_summary(pr_rows)

    # DN
    dn_rows = frappe.db.sql(f"""
        SELECT 
            dni.parent, 
            dn.custom_bc_document_type as bc_type, 
            dn.custom_bc_registration_no as bc_no, 
            dni.item_code, 
            dni.qty
        FROM `tabDelivery Note Item` dni
        INNER JOIN `tabDelivery Note` dn ON dn.name = dni.parent
        WHERE dn.docstatus = 1 {'AND dn.custom_bc_document_type = %(bc)s' if bc_type_f else ''}
    """, {"bc": bc_type_f}, as_dict=True)
    add_to_summary(dn_rows)
    
    # SE
    se_rows = frappe.db.sql(f"""
        SELECT 
            sed.parent, 
            se.custom_bc_document_type as bc_type, 
            se.custom_bc_registration_no as bc_no, 
            sed.item_code, 
            sed.qty
        FROM `tabStock Entry Detail` sed
        INNER JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE se.docstatus = 1 {'AND se.custom_bc_document_type = %(bc)s' if bc_type_f else ''}
    """, {"bc": bc_type_f}, as_dict=True)
    add_to_summary(se_rows)

    # Convert sets to sorted lists
    for k in summary:
        summary[k]["docs"] = sorted(list(summary[k]["docs"]))

    return summary
