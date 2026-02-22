// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.query_reports["Laporan Pemasukan Barang Bea Cukai"] = {
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
            "fieldname": "bc_type",
            "label": __("Tipe Dok. Pabean"),
            "fieldtype": "Select",
            "options": "Semua\nBC23\nBC40\nBC16\nBC262\nLainnya",
            "default": "Semua",
        },
        {
            "fieldname": "supplier",
            "label": __("Pengirim Barang (Supplier)"),
            "fieldtype": "Data",
        },
        {
            "fieldname": "item_code",
            "label": __("Kode Barang"),
            "fieldtype": "Link",
            "options": "Item",
        },
    ],
};
