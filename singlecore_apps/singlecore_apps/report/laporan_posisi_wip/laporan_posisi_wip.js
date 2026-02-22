// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.query_reports["Laporan Posisi WIP"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Perusahaan"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1,
        },
        {
            "fieldname": "warehouse",
            "label": __("Gudang WIP"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "get_query": function () {
                return {
                    filters: {
                        "is_group": 0
                    }
                };
            }
        },
        {
            "fieldname": "item_code",
            "label": __("Kode Barang"),
            "fieldtype": "Link",
            "options": "Item",
        },
    ],
};
