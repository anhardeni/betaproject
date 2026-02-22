# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe import _

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
        {"label": _("Gudang WIP"),        "fieldname": "warehouse",        "fieldtype": "Link",         "width": 160, "options": "Warehouse"},
        {"label": _("Qty di WIP"),        "fieldname": "qty",              "fieldtype": "Float",        "width": 110},
        {"label": _("Valuasi"),           "fieldname": "valuation",        "fieldtype": "Currency",     "width": 130, "options": "currency"},
    ]

def get_data(filters):
    company = filters.get("company")
    warehouse = filters.get("warehouse")
    item_code = filters.get("item_code")

    params = {"company": company}
    cond = "bin.actual_qty > 0"
    
    if company:
        cond += " AND wh.company = %(company)s"
    
    if warehouse:
        cond += " AND bin.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
    else:
        # If no warehouse selected, try to find warehouses that contain 'WIP' or 'PROSES' or 'PRODUKSI'
        cond += " AND (wh.name LIKE '%%WIP%%' OR wh.name LIKE '%%PROSES%%' OR wh.name LIKE '%%PRODUKSI%%' OR wh.name LIKE '%%PROCESS%%')"

    if item_code:
        cond += " AND bin.item_code = %(item_code)s"
        params["item_code"] = item_code

    sql = f"""
        SELECT 
            bin.item_code,
            it.item_name,
            it.stock_uom as uom,
            bin.warehouse,
            bin.actual_qty as qty,
            bin.valuation_rate * bin.actual_qty as valuation
        FROM `tabBin` bin
        INNER JOIN `tabItem` it ON it.name = bin.item_code
        INNER JOIN `tabWarehouse` wh ON wh.name = bin.warehouse
        WHERE {cond}
        ORDER BY bin.warehouse, bin.item_code
    """
    
    raw = frappe.db.sql(sql, params, as_dict=True)
    
    for idx, row in enumerate(raw, 1):
        row["no"] = idx
        
    return raw
