// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('HEADER V2', {
	refresh: function(frm) {
			frm.add_custom_button(__('My Custom Action-1'), function() {
				frappe.call({
					method: 'my_app.api.my_custom_server_action',
					args: {},
					callback: function(response) {
						frappe.msgprint(response.message);
					}
				});
			}, __('Custom Actions'));


			frm.add_custom_button(__('My Custom Action-2'), function() {
				frappe.call({
					method: 'singlecore_apps.api.get_nested_data_all',
					args: {},
					callback: function(response) {
						frappe.msgprint(response.message);
					}
				});
			}, __('Custom Actions'));



		}
	});
	

