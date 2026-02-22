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
        {"label": _("No"),               "fieldname": "no",              "fieldtype": "Int",          "width": 50},
        {"label": _("Kode Barang"),        "fieldname": "item_code",       "fieldtype": "Link",         "width": 130, "options": "Item"},
        {"label": _("Nama Barang"),        "fieldname": "item_name",       "fieldtype": "Data",         "width": 200},
        {"label": _("Satuan"),            "fieldname": "uom",             "fieldtype": "Link",         "width": 80,  "options": "UOM"},
        {"label": _("Saldo Awal"),        "fieldname": "saldo_awal",      "fieldtype": "Float",        "width": 110},
        {"label": _("Pemasukan"),         "fieldname": "pemasukan",       "fieldtype": "Float",        "width": 110},
        {"label": _("Pengeluaran"),       "fieldname": "pengeluaran",     "fieldtype": "Float",        "width": 110},
        {"label": _("Penyesuaian"),       "fieldname": "adjustment",      "fieldtype": "Float",        "width": 110},
        {"label": _("Saldo Akhir"),       "fieldname": "saldo_akhir",     "fieldtype": "Float",        "width": 110},
        {"label": _("Opname (Physical)"),  "fieldname": "opname",          "fieldtype": "Float",        "width": 110},
        {"label": _("Selisih"),           "fieldname": "selisih",         "fieldtype": "Float",        "width": 110},
        {"label": _("Keterangan"),        "fieldname": "keterangan",      "fieldtype": "Small Text",   "width": 150},
    ]

def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    company = filters.get("company")
    warehouse = filters.get("warehouse")
    item_group = filters.get("item_group")
    item_code = filters.get("item_code")

    item_list = get_items(item_group, item_code)
    
    move_data = get_movement_data(from_date, to_date, company, warehouse)
    opening_data = get_opening_balances(from_date, company, warehouse)
    opname_data = get_opname_data(from_date, to_date, company, warehouse)

    data = []
    for idx, item in enumerate(item_list, start=1):
        code = item.name
        opening = opening_data.get(code, 0)
        item_moves = move_data.get(code, {"in": 0, "out": 0, "adj": 0})
        pemasukan = item_moves["in"]
        pengeluaran = item_moves["out"]
        adjustment = item_moves["adj"]
        saldo_akhir = opening + pemasukan - pengeluaran + adjustment
        opname = opname_data.get(code, saldo_akhir)
        selisih = opname - saldo_akhir
        
        if opening == 0 and pemasukan == 0 and pengeluaran == 0 and adjustment == 0 and saldo_akhir == 0:
            continue

        data.append({
            "no": idx,
            "item_code": code,
            "item_name": item.item_name,
            "uom": item.stock_uom,
            "saldo_awal": opening,
            "pemasukan": pemasukan,
            "pengeluaran": pengeluaran,
            "adjustment": adjustment,
            "saldo_akhir": saldo_akhir,
            "opname": opname,
            "selisih": selisih,
            "keterangan": ""
        })
    for i, row in enumerate(data, 1):
        row["no"] = i
    return data

def get_items(item_group, item_code):
    cond = {"disabled": 0}
    if item_group: cond["item_group"] = item_group
    if item_code: cond["name"] = item_code
    return frappe.get_all("Item", filters=cond, fields=["name", "item_name", "stock_uom"])

def get_opening_balances(from_date, company, warehouse):
    params = {"from_date": from_date}
    cond = "sle.posting_date < %(from_date)s AND sle.is_cancelled = 0"
    if company:
        cond += " AND sle.company = %(company)s"
        params["company"] = company
    if warehouse:
        cond += " AND sle.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
    sql = f"SELECT sle.item_code, SUM(sle.actual_qty) as balance FROM `tabStock Ledger Entry` sle WHERE {cond} GROUP BY sle.item_code"
    res = frappe.db.sql(sql, params, as_dict=True)
    return {r.item_code: flt(r.balance) for r in res}

def get_movement_data(from_date, to_date, company, warehouse):
    params = {"from_date": from_date, "to_date": to_date}
    cond = "sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.is_cancelled = 0"
    if company:
        cond += " AND sle.company = %(company)s"
        params["company"] = company
    if warehouse:
        cond += " AND sle.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
    sql = f"SELECT sle.item_code, sle.actual_qty, sle.voucher_type FROM `tabStock Ledger Entry` sle WHERE {cond}"
    res = frappe.db.sql(sql, params, as_dict=True)
    summary = {}
    for r in res:
        code = r.item_code
        qty = flt(r.actual_qty)
        vtype = r.voucher_type
        if code not in summary: summary[code] = {"in": 0, "out": 0, "adj": 0}
        if vtype == "Stock Reconciliation": summary[code]["adj"] += qty
        elif qty > 0: summary[code]["in"] += qty
        else: summary[code]["out"] += abs(qty)
    return summary

def get_opname_data(from_date, to_date, company, warehouse):
    params = {"from_date": from_date, "to_date": to_date}
    cond = "sr.docstatus = 1 AND sr.posting_date BETWEEN %(from_date)s AND %(to_date)s"
    if company:
        cond += " AND sr.company = %(company)s"
        params["company"] = company
    sql = f"SELECT sri.item_code, sri.qty as physical_qty FROM `tabStock Reconciliation` sr INNER JOIN `tabStock Reconciliation Item` sri ON sri.parent = sr.name WHERE {cond} ORDER BY sr.posting_date DESC, sr.posting_time DESC"
    res = frappe.db.sql(sql, params, as_dict=True)
    opnames = {}
    for r in res:
        if r.item_code not in opnames: opnames[r.item_code] = flt(r.physical_qty)
    return opnames
