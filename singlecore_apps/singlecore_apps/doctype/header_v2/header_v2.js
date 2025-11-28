// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

// Include the Barang Manager
frappe.require('/assets/singlecore_apps/js/header_v2_barang_manager.js');

frappe.ui.form.on('HEADER V2', {
	refresh: function (frm) {
		// Add Barang Manager Button (PRIMARY BUTTON)
		if (frm.doc.name) {
			frm.add_custom_button(__('🛒 Manage Barang'), function () {
				show_barang_manager(frm);
			}, __('Actions')).addClass('btn-primary');
		}

		// Original buttons
		frm.add_custom_button(__('My Custom Action-1'), function () {
			frappe.call({
				method: 'my_app.api.my_custom_server_action',
				args: {},
				callback: function (response) {
					frappe.msgprint(response.message);
				}
			});
		}, __('Custom Actions'));

		frm.add_custom_button(__('My Custom Action-2'), function () {
			frappe.call({
				method: 'singlecore_apps.api.get_nested_data_all',
				args: {},
				callback: function (response) {
					frappe.msgprint(response.message);
				}
			});
		}, __('Custom Actions'));
	}
});
