# Copyright (c) 2026, AnharDeni and contributors
# For license information, please see license.txt

import frappe
from frappe import _

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
			"label": _("Nomor Aju"),
			"fieldname": "grn",
			"fieldtype": "Link",
            "options": "HEADER V21",
			"width": 150,
		},
		{
			"label": _("Penerima Barang"),
			"fieldname": "penerima_barang",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Kode"),
			"fieldname": "item_code",
			"fieldtype": "Data",
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
	]

def get_data(filters):
	filters = filters or {}
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	bc_type = filters.get("bc_type")
	supplier = filters.get("supplier")
	item_code = filters.get("item_code")

	bc_map = {
		"BC25": "25",
		"BC30": "30",
		"BC261": "261",
		"BC27": "27",
		"BC28": "28",
		"BC33": "33",
		"BC41": "41",
	}

	conditions = "1=1"
	if from_date:
		conditions += " AND h.tanggal_pernyataan >= %(from_date)s"
	if to_date:
		conditions += " AND h.tanggal_pernyataan <= %(to_date)s"
	
	if bc_type and bc_type != "Semua":
		if bc_type in bc_map:
			conditions += " AND h.kode_dokumen = %(kode_dokumen)s"
		elif bc_type == "Lainnya":
			conditions += " AND h.kode_dokumen NOT IN ('25', '30', '261', '27', '28', '33', '41')"
	
	if supplier:
		conditions += " AND ent.nama_entitas LIKE %(supplier)s"
	if item_code:
		conditions += " AND b.kode_barang LIKE %(item_code)s"
    
	query = f"""
		SELECT
			IFNULL(csl.nopen_date, h.tanggal_pernyataan) AS tanggal,
			CONCAT('BC', h.kode_dokumen) AS data_dok_pabean,
			IFNULL(csl.nopen, 'Belum Ada Nopen') AS no_daftar,
			csl.nopen_date AS tgl_daftar,
			h.name AS grn,
			ent.nama_entitas AS penerima_barang,
			b.kode_barang AS item_code,
			b.uraian AS item_name,
			b.jumlah_satuan AS qty,
			b.kode_satuan AS uom,
			h.kode_valuta AS currency,
			b.harga_satuan AS rate,
			CONCAT('BC', h.kode_dokumen) AS jenis
		FROM
			`tabHEADER V21` h
		INNER JOIN
			`tabBARANG V1` b ON b.nomoraju = h.name
		LEFT JOIN
			`tabENTITAS` ent ON ent.nomoraju = h.name AND ent.kode_entitas = '8' /* Catatan: '1' adalah importir di pabean pemasukan, di pengeluaran seperti BC30, '8' adalah Penerima */
		LEFT JOIN
			`tabCustoms Status Log` csl ON csl.no_aju = h.nomoraju
		WHERE
			{conditions}
		ORDER BY
			csl.nopen_date DESC, h.name ASC
	"""
	data = frappe.db.sql(query, {
		"from_date": from_date,
		"to_date": to_date,
		"kode_dokumen": bc_map.get(bc_type) if bc_type in bc_map else None,
		"supplier": f"%{supplier}%" if supplier else None,
		"item_code": f"%{item_code}%" if item_code else None
	}, as_dict=True)

	# Add running number
	for idx, row in enumerate(data, start=1):
		row["no"] = idx
	return data
