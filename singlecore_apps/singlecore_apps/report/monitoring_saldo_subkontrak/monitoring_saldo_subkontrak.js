// Copyright (c) 2026, Singlecore and contributors
// For license information, please see license.txt

frappe.query_reports["Monitoring Saldo Subkontrak"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("Dari Tanggal"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
		},
		{
			"fieldname": "to_date",
			"label": __("Sampai Tanggal"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "skenario",
			"label": __("Skenario"),
			"fieldtype": "Select",
			"options": "\nBC 261 → BC 262 (Subkontrak Umum)\nBC 27 → BC 27 (Subkontrak Antar KB)"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nOutstanding\nSettled",
			"default": "Outstanding"
		},
		{
			"fieldname": "vendor",
			"label": __("Vendor / Partner"),
			"fieldtype": "Link",
			"options": "Supplier"
		}
	]
};
