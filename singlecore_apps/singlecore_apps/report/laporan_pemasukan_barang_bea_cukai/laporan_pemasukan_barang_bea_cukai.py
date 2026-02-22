# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("No"),
            "fieldname": "no",
            "fieldtype": "Int",
            "width": 50,
        },
        {
            "label": _("Tanggal"),
            "fieldname": "tanggal",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Data Dok Pabean"),
            "fieldname": "data_dok_pabean",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("No. Daftar"),
            "fieldname": "no_daftar",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Tgl. Daftar"),
            "fieldname": "tgl_daftar",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Bukti Penerimaan / GRN"),
            "fieldname": "grn",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Pengirim Barang"),
            "fieldname": "pengirim_barang",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Kode"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 130,
        },
        {
            "label": _("Nama Barang"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Jumlah"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": _("Satuan"),
            "fieldname": "uom",
            "fieldtype": "Data",
            "width": 80,
        },
        {
            "label": _("Curr"),
            "fieldname": "currency",
            "fieldtype": "Data",
            "width": 60,
        },
        {
            "label": _("Harga"),
            "fieldname": "rate",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": _("Jenis"),
            "fieldname": "jenis",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Sumber"),
            "fieldname": "sumber",
            "fieldtype": "Data",
            "width": 80,
        },
    ]


def get_data(filters):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    bc_type = filters.get("bc_type") or "Semua"
    supplier_filter = filters.get("supplier") or ""
    item_code_filter = filters.get("item_code") or ""

    rows = []
    rows += get_purchase_receipt_data(from_date, to_date, bc_type, supplier_filter, item_code_filter)
    rows += get_stock_entry_data(from_date, to_date, bc_type, item_code_filter)

    # Sort by posting date
    rows.sort(key=lambda r: (r.get("tanggal") or ""))

    # Add running number
    for idx, row in enumerate(rows, start=1):
        row["no"] = idx

    return rows


def get_purchase_receipt_data(from_date, to_date, bc_type, supplier_filter, item_code_filter):
    conditions = "pr.docstatus = 1"
    if from_date:
        conditions += " AND pr.posting_date >= %(from_date)s"
    if to_date:
        conditions += " AND pr.posting_date <= %(to_date)s"
    if bc_type and bc_type != "Semua":
        conditions += " AND pr.custom_bc_document_type = %(bc_type)s"
    if supplier_filter:
        conditions += " AND (pr.supplier LIKE %(supplier_like)s OR pr.supplier_name LIKE %(supplier_like)s)"
    if item_code_filter:
        conditions += " AND pri.item_code = %(item_code)s"

    params = {
        "from_date": from_date,
        "to_date": to_date,
        "bc_type": bc_type if bc_type != "Semua" else None,
        "supplier_like": "%" + supplier_filter + "%" if supplier_filter else None,
        "item_code": item_code_filter or None,
    }

    sql = """
        SELECT
            pr.posting_date                                         AS tanggal,
            COALESCE(pr.custom_bc_document_type, '')               AS data_dok_pabean,
            COALESCE(pr.custom_bc_registration_no, '')             AS no_daftar,
            pr.custom_bc_registration_date                         AS tgl_daftar,
            COALESCE(NULLIF(pr.custom_grn_ref, ''), pr.name)       AS grn,
            COALESCE(NULLIF(pr.supplier_name, ''), pr.supplier)    AS pengirim_barang,
            pri.item_code                                           AS item_code,
            pri.item_name                                           AS item_name,
            pri.qty                                                 AS qty,
            pri.uom                                                 AS uom,
            COALESCE(pr.currency, '')                              AS currency,
            COALESCE(pri.rate, 0)                                   AS rate,
            COALESCE(pr.custom_bc_document_type, '')               AS jenis,
            'PR'                                                    AS sumber
        FROM
            `tabPurchase Receipt` pr
            INNER JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
        WHERE {conditions}
        ORDER BY pr.posting_date, pr.name, pri.idx
    """.format(conditions=conditions)

    return frappe.db.sql(sql, params, as_dict=True)


def get_stock_entry_data(from_date, to_date, bc_type, item_code_filter):
    conditions = "se.docstatus = 1 AND se.stock_entry_type = 'Material Receipt'"
    if from_date:
        conditions += " AND se.posting_date >= %(from_date)s"
    if to_date:
        conditions += " AND se.posting_date <= %(to_date)s"
    if bc_type and bc_type != "Semua":
        conditions += " AND se.custom_bc_document_type = %(bc_type)s"
    if item_code_filter:
        conditions += " AND sed.item_code = %(item_code)s"

    params = {
        "from_date": from_date,
        "to_date": to_date,
        "bc_type": bc_type if bc_type != "Semua" else None,
        "item_code": item_code_filter or None,
    }

    sql = """
        SELECT
            se.posting_date                                         AS tanggal,
            COALESCE(se.custom_bc_document_type, '')               AS data_dok_pabean,
            COALESCE(se.custom_bc_registration_no, '')             AS no_daftar,
            se.custom_bc_registration_date                         AS tgl_daftar,
            COALESCE(NULLIF(se.custom_grn_ref, ''), se.name)       AS grn,
            '-'                                                     AS pengirim_barang,
            sed.item_code                                           AS item_code,
            COALESCE(it.item_name, sed.item_code)                  AS item_name,
            sed.qty                                                 AS qty,
            sed.uom                                                 AS uom,
            COALESCE(se.custom_currency, '')                       AS currency,
            COALESCE(sed.basic_rate, 0)                            AS rate,
            COALESCE(se.custom_bc_document_type, '')               AS jenis,
            'SE'                                                    AS sumber
        FROM
            `tabStock Entry` se
            INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
            LEFT  JOIN `tabItem` it ON it.name = sed.item_code
        WHERE {conditions}
        ORDER BY se.posting_date, se.name, sed.idx
    """.format(conditions=conditions)

    return frappe.db.sql(sql, params, as_dict=True)
