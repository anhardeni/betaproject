// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.query_reports["Laporan Pengeluaran Barang"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("Dari Tanggal"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1,
        },
        {
            "fieldname": "to_date",
            "label": __("Sampai Tanggal"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_end(),
            "reqd": 1,
        },
        {
            "fieldname": "company",
            "label": __("Perusahaan"),
            "fieldtype": "Link",
            "options": "Company",
        },
        {
            "fieldname": "warehouse",
            "label": __("Gudang Asal"),
            "fieldtype": "Link",
            "options": "Warehouse",
        },
        {
            "fieldname": "category",
            "label": __("Kategori"),
            "fieldtype": "Select",
            "options": "\nMutasi antar Gudang\nKeluar ke Produksi\nDN (Domestik)\nEkspor",
            "default": "",
        },
        {
            "fieldname": "finished_only",
            "label": __("Finished Goods Only"),
            "fieldtype": "Check",
            "default": 0,
        },
        {
            "fieldname": "item_code",
            "label": __("Kode Barang"),
            "fieldtype": "Link",
            "options": "Item",
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
        },
    ],
};
