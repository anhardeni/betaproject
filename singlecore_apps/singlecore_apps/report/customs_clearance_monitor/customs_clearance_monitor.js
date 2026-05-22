// Copyright (c) 2026, Antigravity and contributors
// For license information, please see license.txt

frappe.query_reports["Customs Clearance Monitor"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "doctype_type",
			"label": __("Jenis Dokumen"),
			"fieldtype": "Select",
			"options": "\n16\n28\n23\n25\n261\n262\n27\n20\n30\n40\n41\n521"
		},
		{
			"fieldname": "bc_status",
			"label": __("Status BC"),
			"fieldtype": "Select",
			"options": "\nPending\nRegistered\nRejected\nCompleted\nOn Hold\nAction Required: NPD"
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "bc_status") {
			if (data.bc_status == "Action Required: NPD") {
				value = "<span style='color:orange; font-weight:bold;'>" + value + "</span>";
			} else if (data.bc_status == "Completed") {
				value = "<span style='color:green; font-weight:bold;'>" + value + "</span>";
			} else if (data.bc_status == "Rejected") {
				value = "<span style='color:red; font-weight:bold;'>" + value + "</span>";
			}
		}

		if (column.fieldname == "jalur") {
			if (data.jalur == "Hijau") {
				value = "<span style='color:green; font-weight:bold;'>" + value + "</span>";
			} else if (data.jalur == "Kuning") {
				value = "<span style='color:orange; font-weight:bold;'>" + value + "</span>";
			} else if (data.jalur == "Merah") {
				value = "<span style='color:red; font-weight:bold;'>" + value + "</span>";
			}
		}

		if (column.fieldname == "no_aju" && data.is_hanging) {
			value = "<span style='background-color: #ffcccc; display: block;'>" + value + " (HANGING?)</span>";
		}

		return value;
	}
};
