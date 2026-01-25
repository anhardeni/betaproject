// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

// Include the Barang Manager
frappe.require('/assets/singlecore_apps/js/header_v2_barang_manager.js');

const BC_SETTINGS = {
	'16': { label: 'BC16', btn: 'btn-success', suffix: 'bc16' },
	'20': { label: 'BC20', btn: 'btn-info', suffix: 'bc20' },
	'23': { label: 'BC23', btn: 'btn-warning', suffix: 'bc23' },
	'25': { label: 'BC25', btn: 'btn-secondary', suffix: 'bc25' },
	'27': { label: 'BC27', btn: 'btn-success', suffix: 'bc27' },
	'28': { label: 'BC28', btn: 'btn-success', suffix: 'bc28' },
	'30': { label: 'BC30', btn: 'btn-info', suffix: 'bc30' },
	'33': { label: 'BC33', btn: 'btn-primary', suffix: 'bc33' },
	'40': { label: 'BC40', btn: 'btn-warning', suffix: 'bc40' },
	'41': { label: 'BC41', btn: 'btn-secondary', suffix: 'bc41' },
	'262': { label: 'BC262', btn: 'btn-info', suffix: 'bc262' },
	'261': { label: 'BC261', btn: 'btn-info', suffix: 'bc261' },
	'511': { label: 'FTZ01-1', btn: 'btn-success', suffix: 'ftz011' },
	'512': { label: 'FTZ01-2', btn: 'btn-success', suffix: 'ftz012' },
	'513': { label: 'FTZ01-3', btn: 'btn-success', suffix: 'ftz013' },
	'331': { label: 'P3BET', btn: 'btn-success', suffix: 'p3bet' }
};

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

			// Context-aware Export & Validation Buttons
			const bc_type = frm.doc.kode_dokumen;
			const setting = BC_SETTINGS[bc_type];
			if (setting) {
				frm.add_custom_button(__(`📄 Export ${setting.label} JSON`), function () {
					const url = `/api/method/singlecore_apps.api.get_ceisa_${setting.suffix}_json?nomor_aju=${frm.doc.nomoraju || frm.doc.name}`;
					window.open(url, '_blank');
				}, __('Actions')).addClass(setting.btn);

				frm.add_custom_button(__(`✅ Check ${setting.label} Schema`), () => validate_bc_schema(frm, setting.label, setting.suffix), __('Actions')).addClass('btn-primary');
			}

			frm.add_custom_button(__("🌍 JSON Export TO Negara"), function () {
				frappe.prompt("Pilih negara:", (country) => {
					frappe.call({
						method: "singlecore_apps.api.export_to_country",
						args: { header_name: frm.doc.name, country_code: country },
						callback: (r) => {
							let json = JSON.stringify(r.message, null, 2);
							download_json(json, `${frm.doc.nomoraju}_${country}.json`);
						}
					});
				});
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
		const setting = BC_SETTINGS[frm.doc.kode_dokumen];
		const label = setting ? setting.label : 'this';
		frappe.confirm(`Are you sure you want to send this <b>${label}</b> document to Beacukai?`, function () {
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

// Unified Validation Helper
function validate_bc_schema(frm, label, suffix) {
	const nomor_aju = frm.doc.nomoraju || frm.doc.name;
	frappe.call({
		method: `singlecore_apps.api.ceisa_export.validate_${suffix}_export`,
		args: { nomor_aju: nomor_aju },
		freeze: true,
		freeze_message: __(`Validating ${label} JSON against schema...`),
		callback: function (r) {
			if (!r.message) {
				frappe.msgprint({
					title: __('Error'),
					message: __('No response received from server'),
					indicator: 'red'
				});
				return;
			}

			let result = r.message;
			if (result.valid) {
				frappe.msgprint({
					title: __('Schema Validation'),
					message: result.message || `✅ BC${bc_type} JSON is valid!`,
					indicator: 'green'
				});
			} else if (result.errors) {
				let error_html = `
					<table class="table table-bordered table-hover" style="font-size: 0.9em;">
						<thead>
							<tr class="active">
								<th style="width: 30%;">${__('Field Path')}</th>
								<th>${__('Error')}</th>
							</tr>
						</thead>
						<tbody>
				`;

				result.errors.forEach(err => {
					error_html += `
						<tr>
							<td><code style="word-break: break-all;">${err.path}</code></td>
							<td>${err.message}</td>
						</tr>
					`;
				});

				error_html += '</tbody></table>';

				frappe.msgprint({
					title: __('Schema Validation Failed'),
					message: error_html,
					indicator: 'red',
					wide: true
				});
			} else {
				frappe.msgprint({
					title: __('Schema Validation Failed'),
					message: '<strong>Error:</strong> ' + (result.error || 'Unknown error'),
					indicator: 'red',
					wide: true
				});
			}
		}
	});
}
