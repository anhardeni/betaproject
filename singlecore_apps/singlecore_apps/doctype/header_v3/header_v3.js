// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('Header V3', {
	setup: function (frm) {
		frm.set_query('kode_tujuan_pengiriman', function () {
			return {
				filters: {
					'kode_dokumen': frm.doc.kode_dokumen
				}
			};
		});
	}
});
