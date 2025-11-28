// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

// Include the Barang Manager
frappe.require('/assets/singlecore_apps/js/header_v2_barang_manager.js');

frappe.ui.form.on('HEADER V21', {
	refresh: function (frm) {
		// Add Barang Manager Button
		if (frm.doc.name) {
			frm.add_custom_button(__('🛒 Manage Barang'), function () {
				show_barang_manager(frm);
			}, __('Actions')).addClass('btn-primary');

			frm.add_custom_button(__('📄 Export CEISA JSON'), function () {
				let nomor_aju = frm.doc.nomoraju || frm.doc.name;
				let url = `/api/method/singlecore_apps.api.get_ceisa_bc20_json?nomor_aju=${nomor_aju}`;
				window.open(url, '_blank');
			}, __('Actions'));

			frm.add_custom_button(__('📥 Import Excel'), function () {
				new frappe.ui.FileUploader({
					method: 'singlecore_apps.api.import_ceisa_excel',
					make_attachments: false,
					on_success: (file_doc) => {
						// This is for standard upload, but we want to process content directly or via API
						// Since we need to send file content to our API, let's use a custom dialog
					}
				});

				// Custom Dialog for direct processing
				let d = new frappe.ui.Dialog({
					title: 'Import CEISA Excel',
					fields: [
						{
							label: 'Select Excel File',
							fieldname: 'file',
							fieldtype: 'Attach',
							reqd: 1
						}
					],
					primary_action_label: 'Import',
					primary_action: function (values) {
						d.hide();
						frappe.call({
							method: 'singlecore_apps.api.import_ceisa_excel',
							args: {
								file_data: values.file
							},
							callback: function (r) {
								if (r.message && r.message.status === 'success') {
									frappe.msgprint(__('Import Successful: ' + r.message.message));
									frm.reload_doc();
								} else {
									frappe.msgprint(__('Import Failed: ' + (r.message ? r.message.message : 'Unknown error')));
								}
							}
						});
					}
				});
				d.show();
			}, __('Actions'));
		}
	}
});
