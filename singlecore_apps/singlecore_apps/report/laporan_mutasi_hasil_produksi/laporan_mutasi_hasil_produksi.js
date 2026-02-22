// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.query_reports["Laporan Mutasi Hasil Produksi"] = {
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
            "default": frappe.defaults.get_user_default("Company"),
        },
        {
            "fieldname": "warehouse",
            "label": __("Gudang"),
            "fieldtype": "Link",
            "options": "Warehouse",
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "default": "Finished Goods",
        },
        {
            "fieldname": "item_code",
            "label": __("Kode Barang"),
            "fieldtype": "Link",
            "options": "Item",
        },
    ],
};
