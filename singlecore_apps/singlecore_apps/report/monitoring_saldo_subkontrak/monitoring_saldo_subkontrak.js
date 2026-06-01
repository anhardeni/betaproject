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
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname === "status" && data) {
			if (data.status === "Settled") {
				value = `<span class="indicator-pill green" style="font-weight: 600; display: inline-block; padding: 2px 8px; border-radius: 12px; background: #e6f4ea; color: #137333;">🟢 Lunas (Settled)</span>`;
			} else {
				if (data.aging < 0) {
					value = `<span class="indicator-pill red" style="font-weight: 600; display: inline-block; padding: 2px 8px; border-radius: 12px; background: #fce8e6; color: #c5221f;">🔴 Terlambat (Overdue)</span>`;
				} else if (data.aging <= 7) {
					value = `<span class="indicator-pill orange" style="font-weight: 600; display: inline-block; padding: 2px 8px; border-radius: 12px; background: #fef7e0; color: #b06000;">🟡 Kritis (H-${data.aging})</span>`;
				} else {
					value = `<span class="indicator-pill blue" style="font-weight: 600; display: inline-block; padding: 2px 8px; border-radius: 12px; background: #e8f0fe; color: #1a73e8;">🔵 Outstanding</span>`;
				}
			}
		}
		
		if (column.fieldname === "aging" && data) {
			if (data.status === "Settled") {
				value = `<span style="color: #80868b; font-style: italic;">-</span>`;
			} else {
				if (data.aging < 0) {
					value = `<span style="color: #d93025; font-weight: bold;">${Math.abs(data.aging)} hari lewat</span>`;
				} else if (data.aging <= 7) {
					value = `<span style="color: #e37400; font-weight: bold;">${data.aging} hari sisa</span>`;
				} else {
					value = `<span style="color: #1e8e3e; font-weight: 500;">${data.aging} hari</span>`;
				}
			}
		}
		
		return value;
	}
};

