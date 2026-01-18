// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

// Include the Barang Manager
frappe.require('/assets/singlecore_apps/js/header_v2_barang_manager.js');

frappe.ui.form.on('HEADER V21', {
	refresh: function (frm) {
		// Change background color
		frm.page.wrapper.find('.layout-main-section').css('background-color', '#F3F4F6');

		// Add Barang Manager Button
		if (frm.doc.name) {
			add_beacukai_actions(frm);
			frm.add_custom_button(__('🛒 Manage Barang'), function () {
				show_barang_manager(frm);
			}, __('Actions')).addClass('btn-primary');

			frm.add_custom_button(__('📄 Export PIB BC20 JSON'), function () {
				let nomor_aju = frm.doc.nomoraju || frm.doc.name;
				let url = `/api/method/singlecore_apps.api.get_ceisa_bc20_json?nomor_aju=${nomor_aju}`;
				window.open(url, '_blank');
			}, __('Actions')).addClass('btn-info');

			frm.add_custom_button(__('📄 Export BC27 JSON'), function () {
				let nomor_aju = frm.doc.nomoraju || frm.doc.name;
				let url = `/api/method/singlecore_apps.api.get_ceisa_bc27_json?nomor_aju=${nomor_aju}`;
				window.open(url, '_blank');
			}, __('Actions')).addClass('btn-success');

			frm.add_custom_button(__('📥 Import Excel'), function () {
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
					primary_action_label: 'Start Check (Simulation)',
					primary_action: function (values) {
						d.hide();
						// Step 1: DRY RUN
						frappe.call({
							method: 'singlecore_apps.api.import_ceisa_excel',
							args: {
								file_data: values.file,
								dry_run: 1
							},
							freeze: true,
							freeze_message: __('Unpacking and Verifying Data...'),
							callback: function (r) {
								if (r.message && r.message.status === 'success') {
									// Step 2: Confirmation
									let msg = r.message.message;
									frappe.confirm(
										msg + '<div class="alert alert-warning">Do you want to PROCEED and SAVE this data?</div>',
										function () {
											// Step 3: REAL RUN
											frappe.call({
												method: 'singlecore_apps.api.import_ceisa_excel',
												args: {
													file_data: values.file,
													dry_run: 0
												},
												freeze: true,
												freeze_message: __('Saving Data...'),
												callback: function (r2) {
													if (r2.message && r2.message.status === 'success') {
														frappe.msgprint({
															title: __('Import Complete'),
															message: r2.message.message,
															indicator: 'green',
															wide: true
														});
														frm.reload_doc();
													} else {
														frappe.msgprint({
															title: __('Save Failed'),
															message: r2.message ? r2.message.message : 'Unknown error',
															indicator: 'red',
															wide: true
														});
													}
												}
											});
										},
										function () {
											// Cancelled
											frappe.show_alert('Import Cancelled by User');
										}
									).find('.modal-dialog').css('max-width', '800px'); // Widen the confirm modal
								} else {
									// Dry Run Failed (Validation Error or similar)
									frappe.msgprint({
										title: __('Verification Failed'),
										message: r.message ? r.message.message : 'Unknown error',
										indicator: 'red',
										wide: true
									});
								}
							}
						});
					}
				});
				d.show();
			}, __('Actions')).addClass('btn-success');
		}
	}
});

function add_beacukai_actions(frm) {
	frm.add_custom_button(__('🔐 Login Beacukai'), function () {
		let d = new frappe.ui.Dialog({
			title: 'Login Beacukai',
			fields: [
				{
					label: 'Username',
					fieldname: 'username',
					fieldtype: 'Data',
					reqd: 1
				},
				{
					label: 'Password',
					fieldname: 'password',
					fieldtype: 'Password',
					reqd: 1
				}
			],
			primary_action_label: 'Login',
			primary_action: function (values) {
				frappe.call({
					method: 'singlecore_apps.api.login_beacukai',
					args: {
						username: values.username,
						password: values.password
					},
					callback: function (r) {
						if (r.message && r.message.status === 'success') {
							frappe.msgprint('Login Successful');
							d.hide();
						} else {
							frappe.msgprint('Login Failed: ' + (r.message ? r.message.message : 'Unknown error'));
						}
					}
				});
			}
		});
		d.show();
	}, __('Beacukai'));

	frm.add_custom_button(__('📤 Send Document'), function () {
		frappe.confirm('Are you sure you want to send this document to Beacukai?', function () {
			frappe.call({
				method: 'singlecore_apps.api.send_ceisa_document',
				args: {
					docname: frm.doc.nomoraju || frm.doc.name
				},
				freeze: true,
				freeze_message: 'Sending to Beacukai...',
				callback: function (r) {
					if (r.message) {
						frappe.msgprint({
							title: r.message.status === 'success' ? 'Success' : 'Error',
							message: '<pre>' + JSON.stringify(r.message.response, null, 2) + '</pre>',
							indicator: r.message.status === 'success' ? 'green' : 'red',
							wide: true
						});
					}
				}
			});
		});
	}, __('Beacukai'));

	frm.add_custom_button(__('🔄 Check Status'), function () {
		frappe.call({
			method: 'singlecore_apps.api.check_ceisa_status',
			args: {
				nomor_aju: frm.doc.nomoraju || frm.doc.name
			},
			freeze: true,
			callback: function (r) {
				if (r.message) {
					frappe.msgprint({
						title: 'Status',
						message: '<pre>' + JSON.stringify(r.message.response, null, 2) + '</pre>',
						indicator: r.message.status === 'success' ? 'blue' : 'red',
						wide: true
					});
				}
			}
		});
	}, __('Beacukai'));
}
