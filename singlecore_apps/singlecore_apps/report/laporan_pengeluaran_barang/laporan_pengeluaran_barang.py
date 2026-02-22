# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# SE types that mean "Keluar ke Produksi"
PRODUCTION_SE_TYPES = (
    "Material Issue",
    "Material Transfer for Manufacture",
    "Material Consumption for Manufacture",
    "Manufacture",
)


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data


def get_columns():
    return [
        {"label": _("No"),               "fieldname": "no",              "fieldtype": "Int",          "width": 50},
        {"label": _("Kategori"),          "fieldname": "kategori",        "fieldtype": "Data",         "width": 140},
        {"label": _("Data Dok Pabean"),   "fieldname": "data_dok_pabean", "fieldtype": "Data",         "width": 120},
        {"label": _("No. Daftar"),        "fieldname": "no_daftar",       "fieldtype": "Data",         "width": 160},
        {"label": _("Tgl. Daftar"),       "fieldname": "tgl_daftar",      "fieldtype": "Date",         "width": 110},
        {"label": _("Tanggal"),           "fieldname": "tanggal",         "fieldtype": "Date",         "width": 100},
        {"label": _("Tipe Dokumen"),      "fieldname": "tipe_dokumen",    "fieldtype": "Data",         "width": 120},
        {"label": _("No Dokumen"),        "fieldname": "no_dokumen",      "fieldtype": "Data",         "width": 160},
        {"label": _("Gudang Asal"),       "fieldname": "gudang_asal",     "fieldtype": "Link",         "width": 160, "options": "Warehouse"},
        {"label": _("Gudang/Tujuan"),     "fieldname": "gudang_tujuan",   "fieldtype": "Data",         "width": 180},
        {"label": _("Item"),              "fieldname": "item_code",       "fieldtype": "Link",         "width": 130, "options": "Item"},
        {"label": _("Nama Item"),         "fieldname": "item_name",       "fieldtype": "Data",         "width": 200},
        {"label": _("Satuan"),            "fieldname": "uom",             "fieldtype": "Link",         "width": 80,  "options": "UOM"},
        {"label": _("Qty Keluar"),        "fieldname": "qty",             "fieldtype": "Float",        "width": 100},
        {"label": _("Curr"),              "fieldname": "currency",        "fieldtype": "Data",         "width": 60},
        {"label": _("Harga"),             "fieldname": "rate",            "fieldtype": "Currency",     "width": 110, "options": "currency"},
        {"label": _("Nilai"),             "fieldname": "nilai",           "fieldtype": "Currency",     "width": 130, "options": "currency"},
        {"label": _("Customer"),          "fieldname": "customer",        "fieldtype": "Link",         "width": 160, "options": "Customer"},
        {"label": _("Negara Tujuan"),     "fieldname": "negara_tujuan",   "fieldtype": "Data",         "width": 120},
        {"label": _("Keterangan"),        "fieldname": "keterangan",      "fieldtype": "Small Text",   "width": 200},
    ]


def get_data(filters):
    from_date      = filters.get("from_date")
    to_date        = filters.get("to_date")
    company        = filters.get("company")
    warehouse      = filters.get("warehouse")
    category       = filters.get("category") or ""
    finished_only  = filters.get("finished_only")
    item_code      = filters.get("item_code")
    customer_f     = filters.get("customer")

    rows = []

    if not category or category == "Mutasi antar Gudang":
        rows += get_se_rows(
            from_date, to_date, company, warehouse, item_code, finished_only,
            se_types=("Material Transfer",),
            kategori="Mutasi antar Gudang",
        )

    if not category or category == "Keluar ke Produksi":
        rows += get_se_rows(
            from_date, to_date, company, warehouse, item_code, finished_only,
            se_types=PRODUCTION_SE_TYPES,
            kategori="Keluar ke Produksi",
        )

    if not category or category in ("DN (Domestik)", "Ekspor"):
        rows += get_dn_rows(
            from_date, to_date, company, warehouse, item_code, finished_only,
            customer_f, category,
        )

    # Sort: tanggal ASC, kategori, item_code
    rows.sort(key=lambda r: (
        str(r.get("tanggal") or ""),
        r.get("kategori", ""),
        r.get("item_code", ""),
    ))

    # Running number
    for idx, row in enumerate(rows, start=1):
        row["no"] = idx

    return rows


def get_se_rows(from_date, to_date, company, warehouse, item_code, finished_only, se_types, kategori):
    n = len(se_types)
    placeholder = "(" + ",".join([f"%(se_type_{i})s" for i in range(n)]) + ")"
    params = {f"se_type_{i}": t for i, t in enumerate(se_types)}

    cond = f"se.docstatus = 1 AND se.stock_entry_type IN {placeholder}"
    if from_date:
        cond += " AND se.posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        cond += " AND se.posting_date <= %(to_date)s"
        params["to_date"] = to_date
    if company:
        cond += " AND se.company = %(company)s"
        params["company"] = company
    if warehouse:
        cond += " AND sed.s_warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
    if item_code:
        cond += " AND sed.item_code = %(item_code)s"
        params["item_code"] = item_code
    if finished_only:
        cond += " AND it.item_group = 'Finished Goods'"
    
    cond += " AND sed.s_warehouse IS NOT NULL"

    sql = f"""
        SELECT
            se.posting_date                                             AS tanggal,
            se.name                                                     AS no_dokumen,
            se.company                                                  AS company,
            se.custom_bc_document_type                                  AS data_dok_pabean,
            se.custom_bc_registration_no                                AS no_daftar,
            se.custom_bc_registration_date                              AS tgl_daftar,
            sed.s_warehouse                                             AS gudang_asal,
            COALESCE(sed.t_warehouse, se.to_warehouse, '-')             AS gudang_tujuan,
            sed.item_code                                               AS item_code,
            COALESCE(it.item_name, sed.item_code)                       AS item_name,
            sed.qty                                                     AS qty,
            sed.uom                                                     AS uom,
            COALESCE(se.custom_currency, '')                            AS currency,
            COALESCE(sed.basic_rate, 0)                                 AS rate,
            (COALESCE(sed.qty, 0) * COALESCE(sed.basic_rate, 0))        AS nilai,
            se.stock_entry_type                                         AS keterangan
        FROM `tabStock Entry` se
        INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
        LEFT  JOIN `tabItem` it ON it.name = sed.item_code
        WHERE {cond}
    """

    raw = frappe.db.sql(sql, params, as_dict=True)

    result = []
    for r in raw:
        result.append({
            "kategori":      kategori,
            "data_dok_pabean": r.data_dok_pabean,
            "no_daftar":     r.no_daftar,
            "tgl_daftar":    r.tgl_daftar,
            "tanggal":       r.tanggal,
            "tipe_dokumen":  "Stock Entry",
            "no_dokumen":    r.no_dokumen,
            "company":       r.company,
            "gudang_asal":   r.gudang_asal,
            "gudang_tujuan": r.gudang_tujuan,
            "item_code":     r.item_code,
            "item_name":     r.item_name,
            "qty":           r.qty,
            "uom":           r.uom,
            "currency":      r.currency,
            "rate":          r.rate,
            "nilai":         r.nilai,
            "customer":      None,
            "negara_tujuan": None,
            "keterangan":    r.keterangan,
        })
    return result


def get_dn_rows(from_date, to_date, company, warehouse, item_code, finished_only, customer_f, category_filter):
    # Get company country for export detection
    company_countries = {c.name: c.country for c in frappe.db.get_all("Company", fields=["name", "country"])}

    cond = "dn.docstatus = 1 AND dn.is_return = 0"
    params = {}
    if from_date:
        cond += " AND dn.posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        cond += " AND dn.posting_date <= %(to_date)s"
        params["to_date"] = to_date
    if company:
        cond += " AND dn.company = %(company)s"
        params["company"] = company
    if warehouse:
        cond += " AND dni.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
    if item_code:
        cond += " AND dni.item_code = %(item_code)s"
        params["item_code"] = item_code
    if finished_only:
        cond += " AND it.item_group = 'Finished Goods'"
    if customer_f:
        cond += " AND dn.customer = %(customer_f)s"
        params["customer_f"] = customer_f

    sql = f"""
        SELECT
            dn.posting_date                                             AS tanggal,
            dn.name                                                     AS no_dokumen,
            dn.company                                                  AS company,
            dn.custom_bc_document_type                                  AS data_dok_pabean,
            dn.custom_bc_registration_no                                AS no_daftar,
            dn.custom_bc_registration_date                              AS tgl_daftar,
            dni.warehouse                                               AS gudang_asal,
            dn.customer                                                 AS customer,
            dn.customer_name                                            AS customer_name,
            COALESCE(addr.country, '')                                  AS shipping_country,
            dni.item_code                                               AS item_code,
            COALESCE(it.item_name, dni.item_code)                       AS item_name,
            dni.qty                                                     AS qty,
            dni.uom                                                     AS uom,
            dn.currency                                                 AS currency,
            COALESCE(dni.rate, 0)                                       AS rate,
            (COALESCE(dni.qty, 0) * COALESCE(dni.rate, 0))              AS nilai,
            ''                                                          AS keterangan
        FROM `tabDelivery Note` dn
        INNER JOIN `tabDelivery Note Item` dni ON dni.parent = dn.name
        LEFT  JOIN `tabItem` it ON it.name = dni.item_code
        LEFT  JOIN `tabAddress` addr ON addr.name = dn.shipping_address_name
        WHERE {cond}
    """

    raw = frappe.db.sql(sql, params, as_dict=True)

    result = []
    for r in raw:
        company_country = company_countries.get(r.company, "")
        ship_country = r.shipping_country or company_country

        if ship_country and ship_country != company_country:
            kategori = "Ekspor"
        else:
            kategori = "DN (Domestik)"

        if category_filter and category_filter not in ("", kategori):
            continue

        result.append({
            "kategori":      kategori,
            "data_dok_pabean": r.data_dok_pabean,
            "no_daftar":     r.no_daftar,
            "tgl_daftar":    r.tgl_daftar,
            "tanggal":       r.tanggal,
            "tipe_dokumen":  "Delivery Note",
            "no_dokumen":    r.no_dokumen,
            "company":       r.company,
            "gudang_asal":   r.gudang_asal,
            "gudang_tujuan": r.customer_name or r.customer,
            "item_code":     r.item_code,
            "item_name":     r.item_name,
            "qty":           r.qty,
            "uom":           r.uom,
            "currency":      r.currency,
            "rate":          r.rate,
            "nilai":         r.nilai,
            "customer":      r.customer,
            "negara_tujuan": r.shipping_country or None,
            "keterangan":    r.keterangan or "",
        })
    return result
