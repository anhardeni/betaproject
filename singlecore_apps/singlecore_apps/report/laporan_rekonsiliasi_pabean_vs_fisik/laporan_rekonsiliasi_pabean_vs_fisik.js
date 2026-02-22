// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.query_reports["Laporan Rekonsiliasi Pabean vs Fisik"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("Dari Tanggal Daftar BC"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1,
        },
        {
            "fieldname": "to_date",
            "label": __("Sampai Tanggal Daftar BC"),
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
            "fieldname": "bc_type",
            "label": __("Tipe Dokumen BC"),
            "fieldtype": "Select",
            "options": "\nBC23\nBC40\nBC16\nBC25\nBC27\nBC28\nBC30\nBC33\nBC41",
        },
    ],
};
