// Copyright (c) 2023, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('BARANG V1', {
	refresh: function (frm) {
		if (frm.doc.nomoraju) {
			frm.add_custom_button(__('Back to Header V21'), function () {
				frappe.set_route("Form", "HEADER V21", frm.doc.nomoraju);
			});


			if (frm.doc.gambar_barang) {
				frm.add_custom_button(__('📤 Upload Photo to CEISA'), function () {
					frappe.confirm(__('Are you sure you want to upload this product photo to CEISA via H2H?'), function () {
						frappe.call({
							method: 'singlecore_apps.api.ceisa_api.h2h_upload.trigger_h2h_barang_upload',
							args: { barang_name: frm.doc.name },
							freeze: true,
							freeze_message: __('Uploading photo to Beacukai...'),
							callback: function (r) {
								if (r.message && r.message.status === 'success') {
									frappe.show_alert({
										message: __('Product photo uploaded successfully.'),
										indicator: 'green'
									});
								} else {
									console.error("H2H Photo Upload Error:", r.message);
								}
								frm.reload_doc();
							}
						});
					});
				}).attr('style', 'background:#1B5E20;color:#fff;border-color:#0A3D0A;font-weight:600;');
			}
		}
	}
});
