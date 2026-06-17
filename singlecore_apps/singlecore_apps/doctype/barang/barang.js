// Copyright (c) 2023, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('BARANG', {
	refresh: function(frm) {
		frm.add_custom_button(__('Back'), function() {
			if (window.history.length > 1) {
				window.history.back();
			} else {
				frappe.set_route('List', frm.doctype);
			}
		});
	}
});
