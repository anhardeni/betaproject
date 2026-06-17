// Copyright (c) 2023, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('BAHAN BAKU', {
	refresh: function (frm) {
		frm.add_custom_button(__('Back'), function () {
			if (window.history.length > 1) {
				window.history.back();
			} else {
				frappe.set_route('List', frm.doctype);
			}
		});

		if (frm.doc.parent_barang) {
			frm.add_custom_button(__('Back to BARANG V1'), function () {
				frappe.set_route("Form", "BARANG V1", frm.doc.parent_barang);
			});
		}
	}
});
