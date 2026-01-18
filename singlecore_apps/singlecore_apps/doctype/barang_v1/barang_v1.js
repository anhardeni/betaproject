// Copyright (c) 2023, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('BARANG V1', {
	refresh: function (frm) {
		if (frm.doc.nomoraju) {
			frm.add_custom_button(__('Back to Header V21'), function () {
				frappe.set_route("Form", "HEADER V21", frm.doc.nomoraju);
			});

			frm.add_custom_button(__('Back to Barang V1'), function () {
				frappe.set_route("Form", "BARANG V1", frm.doc.nomoraju);
			});

		}
	}
});
