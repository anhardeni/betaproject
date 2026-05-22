// Copyright (c) 2024, AnharDeni and contributors
// For license information, please see license.txt

// Include the Barang Manager
frappe.require('/assets/singlecore_apps/js/header_v2_barang_manager.js');

const BC_SETTINGS = {
	// 🔵 Import / Pemasukan group  — blues
	'16': { label: 'BC16', style: 'background:#1565C0;color:#fff;border-color:#0D47A1;', suffix: 'bc16' },
	'20': { label: 'BC20', style: 'background:#1976D2;color:#fff;border-color:#1565C0;', suffix: 'bc20' },
	'27': { label: 'BC27', style: 'background:#0288D1;color:#fff;border-color:#01579B;', suffix: 'bc27' },
	'28': { label: 'BC28', style: 'background:#006064;color:#fff;border-color:#004D40;', suffix: 'bc28' },
	'40': { label: 'BC40', style: 'background:#283593;color:#fff;border-color:#1A237E;', suffix: 'bc40' },
	// 🟢 Export / Pengeluaran group — greens
	'30': { label: 'BC30', style: 'background:#2E7D32;color:#fff;border-color:#1B5E20;', suffix: 'bc30' },
	'33': { label: 'BC33', style: 'background:#388E3C;color:#fff;border-color:#2E7D32;', suffix: 'bc33' },
	// 🟣 Transfer internal TPB — purples
	'25': { label: 'BC25', style: 'background:#6A1B9A;color:#fff;border-color:#4A148C;', suffix: 'bc25' },
	'262': { label: 'BC262', style: 'background:#7B1FA2;color:#fff;border-color:#6A1B9A;', suffix: 'bc262' },
	'261': { label: 'BC261', style: 'background:#8E24AA;color:#fff;border-color:#7B1FA2;', suffix: 'bc261' },
	// 🟡 Cukai / Special — amber
	'23': { label: 'BC23', style: 'background:#F57F17;color:#fff;border-color:#E65100;', suffix: 'bc23' },
	// 🩵 BC41 — teal
	'41': { label: 'BC41', style: 'background:#00695C;color:#fff;border-color:#004D40;', suffix: 'bc41' },
	// 🔷 FTZ — cyan/dark
	'511': { label: 'FTZ01-1', style: 'background:#00838F;color:#fff;border-color:#006064;', suffix: 'ftz011' },
	'512': { label: 'FTZ01-2', style: 'background:#00796B;color:#fff;border-color:#004D40;', suffix: 'ftz012' },
	'513': { label: 'FTZ01-3', style: 'background:#00695C;color:#fff;border-color:#004D40;', suffix: 'ftz013' },
	// 🟠 P3BET — orange
	'331': { label: 'P3BET', style: 'background:#E65100;color:#fff;border-color:#BF360C;', suffix: 'p3bet' }
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
			}, __('Actions')).attr('style', 'background:#1565C0;color:#fff;border-color:#0D47A1;font-weight:600;');

			// Context-aware Export & Validation Buttons
			const bc_type = frm.doc.kode_dokumen;
			const setting = BC_SETTINGS[bc_type];
			if (setting) {
				frm.add_custom_button(__(`📄 Export ${setting.label} JSON`), function () {
					const url = `/api/method/singlecore_apps.api.get_ceisa_${setting.suffix}_json?nomor_aju=${frm.doc.nomoraju || frm.doc.name}`;
					window.open(url, '_blank');
				}, __('Actions')).attr('style', setting.style + 'font-weight:600;');

				frm.add_custom_button(__(`✅ Check ${setting.label} Schema`), () => validate_bc_schema(frm, setting.label, setting.suffix), __('Actions'))
					.attr('style', 'background:#1B5E20;color:#fff;border-color:#0A3D0A;font-weight:600;');
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
			}, __('Actions')).attr('style', 'background:#004D40;color:#fff;border-color:#00251A;font-weight:600;');

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
			}, __('Actions')).attr('style', 'background:#37474F;color:#fff;border-color:#263238;font-weight:600;');

			// -------------------------------------------------------
			// 📋 Duplicate as New
			//    Deep-clones the current document (+ ALL child tables)
			//    via the server method and redirects to the new doc.
			//    Only shown for saved (non-new) documents.
			// -------------------------------------------------------
			frm.add_custom_button(__('📋 Duplicate as New'), function () {
				frappe.confirm(
					__('Duplicate <b>{0}</b> as a new document (all child tables will be copied)?',
						[frm.doc.name]),
					function () {
						// User confirmed — call server method with spinner
						frappe.call({
							method: 'singlecore_apps.api.duplicate_doc.duplicate_as_new',
							args: {
								doctype: frm.doctype,
								name: frm.doc.name
							},
							freeze: true,
							freeze_message: __('Duplicating document… please wait'),
							callback: function (r) {
								if (r && r.message) {
									const res = r.message;
									// Show success summary (child table row counts etc.)
									frappe.msgprint({
										title: __('Duplicate Created'),
										message: res.summary ||
											__('New document <b>{0}</b> created successfully.', [res.name]),
										indicator: 'green',
										wide: false,
									});
									// Navigate to the new document
									frappe.set_route('Form', res.doctype, res.name);
								}
							},
							error: function (r) {
								// frappe.call already shows a red banner; this is
								// extra detail in case the server returns a message
								const detail = (r && r.message) ? r.message : __('An unexpected error occurred.');
								frappe.msgprint({
									title: __('Duplication Failed'),
									message: detail,
									indicator: 'red',
								});
							}
						});
					}
				);
			}, __('Actions')).attr('style', 'background:#E65100;color:#fff;border-color:#BF360C;font-weight:600;');

			// ── H2H Upload Orchestration ────────────────────────────────
			frm.fields_dict['dokumen'].grid.add_custom_button(__('📤 Upload to CEISA'), function () {
				let selected = frm.fields_dict['dokumen'].grid.get_selected();
				if (selected.length === 0) {
					frappe.msgprint(__('Please select at least one document row to upload.'));
					return;
				}
				
				frappe.confirm(__('Are you sure you want to upload {0} document(s) to CEISA via H2H?', [selected.length]), function () {
					selected.forEach(row_name => {
						upload_h2h_row(frm, row_name);
					});
				});
			});
		}
	}
});

/**
 * Trigger H2H upload for a specific DOKUMEN row.
 */
function upload_h2h_row(frm, row_name) {
	frappe.call({
		method: 'singlecore_apps.api.ceisa_api.h2h_upload.trigger_h2h_upload',
		args: { dokumen_row_name: row_name },
		freeze: true,
		freeze_message: __('Uploading document to Beacukai...'),
		callback: function (r) {
			if (r.message && r.message.status === 'success') {
				frappe.show_alert({
					message: __('Document {0} uploaded successfully.', [row_name]),
					indicator: 'green'
				});
			} else {
				// Errors are already logged and stored in the row by the server
				console.error("H2H Upload Error:", r.message);
			}
			frm.reload_doc();
		}
	});
}

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
							frappe.msgprint(r.message.message || 'Login Successful');
							d.hide();
						} else {
							frappe.msgprint({
								title: 'Login Failed',
								message: r.message ? r.message.message : 'Unknown error',
								indicator: 'red'
							});
						}
					}
				});
			}
		});
		d.show();
	}, __('Beacukai')).attr('style', 'background:#37474F;color:#fff;border-color:#263238;');

	frm.add_custom_button(__('🔍 Check with CEISA'), function () {
		check_with_ceisa(frm);
	}, __('Beacukai')).attr('style', 'background:#F57F17;color:#fff;border-color:#E65100;font-weight:600;');

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
	}, __('Beacukai')).attr('style', 'background:#B71C1C;color:#fff;border-color:#7F0000;font-weight:600;');

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
	}, __('Beacukai')).attr('style', 'background:#01579B;color:#fff;border-color:#0D47A1;');
}

// CEISA Live Document Check Handler
function check_with_ceisa(frm) {
	const bc_type = frm.doc.kode_dokumen;
	const setting = BC_SETTINGS[bc_type];
	if (!bc_type || !setting) {
		frappe.msgprint({
			title: __('Unsupported Document Type'),
			message: __('kode_dokumen "{0}" is not supported by this validator.', [bc_type || '(empty)']),
			indicator: 'orange'
		});
		return;
	}

	const nomor_aju = frm.doc.nomoraju || frm.doc.name;
	const label = setting.label;

	frappe.call({
		method: 'singlecore_apps.api.ceisa_export.check_export_with_ceisa',
		args: { nomor_aju: nomor_aju, bc_type: bc_type },
		freeze: true,
		freeze_message: __(`Checking ${label} document with CEISA API…`),
		callback: function (r) {
			const res = r.message;
			if (!res) {
				frappe.msgprint({ title: __('Error'), message: __('No response from server.'), indicator: 'red' });
				return;
			}

			// ── Generation error (JSON build failed) ──────────────────────
			if (res.valid === false && res.error) {
				frappe.msgprint({
					title: __('JSON Generation Error'),
					message: '<strong>' + res.error + '</strong>',
					indicator: 'red',
					wide: true
				});
				return;
			}

			// ── Build display ─────────────────────────────────────────────
			const http_code = res.http_code || '?';
			const data = res.data || {};
			const is_ok = res.status === 'success' && http_code == 200;

			// Try to pull field-level errors from CEISA response structure
			// CEISA typically returns: { status, message, data: { errors: [...] } }
			let ceisa_errors = null;
			if (!is_ok) {
				const inner = data.data || data;
				if (Array.isArray(inner)) ceisa_errors = inner;
				else if (Array.isArray(inner.errors)) ceisa_errors = inner.errors;
				else if (Array.isArray(inner.messages)) ceisa_errors = inner.messages;
			}

			let body = '';

			if (is_ok) {
				// ✅ CEISA accepted the document
				const msg = data.message || data.status || JSON.stringify(data, null, 2);
				body = `<div class="alert alert-success">✅ <strong>CEISA accepted the ${label} document.</strong><br>${msg}</div>`;
			} else if (ceisa_errors && ceisa_errors.length) {
				// ❌ Field-level error table
				body = `<p><strong>HTTP ${http_code}</strong> — CEISA returned ${ceisa_errors.length} error(s):</p>
				<table class="table table-bordered table-hover" style="font-size:0.9em;">
					<thead><tr class="active"><th style="width:35%">${__('Field / Path')}</th><th>${__('Error Message')}</th></tr></thead>
					<tbody>`;
				ceisa_errors.forEach(function (e) {
					const field = e.field || e.path || e.key || '—';
					const msg = e.message || e.msg || e.description || JSON.stringify(e);
					body += `<tr><td><code style="word-break:break-all">${field}</code></td><td>${msg}</td></tr>`;
				});
				body += '</tbody></table>';
			} else {
				// ❌ Generic error — show raw response
				const error_msg = res.message ? `<p style="color: red; margin-bottom: 10px;"><strong>Error:</strong> ${res.message}</p>` : '';
				body = `<p><strong>HTTP ${http_code}</strong></p>\n\t\t\t\t${error_msg}\n\t\t\t\t<pre style="white-space:pre-wrap;font-size:0.85em;">${JSON.stringify(data, null, 2)}</pre>`;
			}

			frappe.msgprint({
				title: __(`CEISA Check — ${label} (HTTP ${http_code})`),
				message: body,
				indicator: is_ok ? 'green' : 'red',
				wide: true
			});
		}
	});
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

