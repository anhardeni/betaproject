// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.query_reports["Laporan Pengeluaran Barang CEISA"] = {
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
            "options": "Semua\nBC25\nBC30\nBC261\nBC27\nBC28\nBC33\nBC41\nLainnya",
            "default": "Semua",
        },
        {
            "fieldname": "supplier",
            "label": __("Penerima Barang (Customer)"),
            "fieldtype": "Data",
        },
        {
            "fieldname": "item_code",
            "label": __("Kode Barang"),
            "fieldtype": "Data",
        },
    ],
};
