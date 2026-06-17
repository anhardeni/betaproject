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

const ALWAYS_VISIBLE_FIELDS = [
	"nomoraju",
	"disclaimer",
	"kode_dokumen",
	"kode_dokumen4digit",
	"kode_kantor",
	"kota_pernyataan",
	"tanggal_pernyataan",
	"nama_pernyataan",
	"jabatan_pernyataan",
	"tgl_jatuh_tempo_subkon",
	"respon_json"
];

const SCHEMA_FIELDS = {
	"20": [ // BC20 - PIB
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "disclaimer", "fob", "freight",
		"harga_penyerahan", "jabatan_pernyataan", "jumlah_tanda_pengaman", "kode_asuransi", "kode_cara_bayar",
		"kode_incoterm", "kode_jenis_ekspor", "kode_jenis_impor", "kode_jenis_nilai", "kode_jenis_pib",
		"kode_kantor", "kode_pelabuhan_muat", "kode_pelabuhan_tujuan", "kode_tps", "kode_tutup_pu",
		"kode_valuta", "kota_pernyataan", "nama_pernyataan", "ndpbm", "nilai_barang", "nilai_incoterm",
		"nilai_maklon", "nomor_bc11", "nomor_pos", "nomor_sub_pos", "nomoraju", "tanggal_bc11",
		"tanggal_pernyataan", "tanggal_tiba", "total_dana_sawit", "vd", "volume",
		"entitas", "kemasan", "kontainer", "komponen_biaya", "dokumen"
	],
	"27": [ // BC27 - TPB TPB
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "dasar_pengenaan_pajak",
		"disclaimer", "freight", "harga_penyerahan", "jabatan_pernyataan", "kode_jenis_tpb", "kode_kantor",
		"kode_kantor_tujuan", "kode_tps", "kode_tujuan_pengiriman", "kode_tujuan_tpb", "kode_valuta",
		"kota_pernyataan", "nama_pernyataan", "ndpbm", "nilai_barang", "nilai_jasa", "nomoraju",
		"ppn_pajak", "ppnbm_pajak", "tanggal_pernyataan", "tarif_ppn_pajak", "tarif_ppnbm_pajak",
		"uang_muka", "vd", "entitas", "kemasan", "kontainer", "pengangkut", "dokumen"
	],
	"23": [ // BC23 - PIB TPB
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "fob", "freight",
		"harga_penyerahan", "jabatan_pernyataan", "kode_asuransi", "kode_incoterm", "kode_jasa_kena_pajak",
		"kode_kantor", "kode_kantor_bongkar", "kode_pelabuhan_bongkar", "kode_pelabuhan_muat",
		"kode_pelabuhan_transit", "kode_tps", "kode_tujuan_tpb", "kode_tutup_pu", "kode_valuta",
		"kota_pernyataan", "nama_pernyataan", "ndpbm", "nilai_barang", "nomor_bc11", "nomor_pos",
		"nomor_sub_pos", "nomoraju", "tanggal_bc11", "tanggal_pernyataan", "tanggal_tiba",
		"entitas", "kemasan", "kontainer", "dokumen"
	],
	"25": [ // BC25 - TPB Lokalan
		"bruto", "cif", "dasar_pengenaan_pajak", "disclaimer", "harga_penyerahan", "jabatan_pernyataan",
		"kode_cara_bayar", "kode_jenis_tpb", "kode_kantor", "kode_lokasi_bayar", "kode_tujuan_pengiriman",
		"kode_valuta", "kota_pernyataan", "nama_pernyataan", "ndpbm", "nomoraju", "ppn_pajak",
		"ppnbm_pajak", "tanggal_pernyataan", "tarif_ppn_pajak", "tarif_ppnbm_pajak", "volume",
		"entitas", "kemasan", "kontainer", "pengangkut", "dokumen"
	],
	"30": [ // BC30 - PEB
		"asuransi", "bruto", "cif", "disclaimer", "flag_curah", "flag_migas", "fob", "freight",
		"jabatan_pernyataan", "kode_asuransi", "kode_cara_bayar", "kode_cara_dagang", "kode_incoterm",
		"kode_jenis_ekspor", "kode_jenis_nilai", "kode_jenis_pengangkutan", "kode_jenis_prosedur",
		"kode_kantor", "kode_kantor_ekspor", "kode_kantor_muat", "kode_kantor_periksa",
		"kode_kategori_ekspor", "kode_lokasi", "kode_negara_tujuan", "kode_pelabuhan_ekspor",
		"kode_pelabuhan_muat", "kode_pelabuhan_tujuan", "kode_tps", "kode_valuta", "kota_pernyataan",
		"nama_pernyataan", "ndpbm", "netto", "nilai_maklon", "nomoraju", "tanggal_ekspor",
		"tanggal_periksa", "tanggal_pernyataan", "total_dana_sawit", "entitas", "kemasan",
		"kontainer", "pengangkut", "bank_devisa", "kesiapan_barang", "dokumen"
	],
	"40": [ // BC40 - TPB Masuk
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "freight", "harga_penyerahan",
		"jabatan_pernyataan", "kode_jenis_tpb", "kode_kantor", "kode_tujuan_pengiriman", "kota_pernyataan",
		"nama_pernyataan", "netto", "nilai_jasa", "nomoraju", "tanggal_pernyataan", "uang_muka",
		"vd", "volume", "entitas", "kemasan", "kontainer", "dokumen"
	],
	"41": [ // BC41 - TPB Keluar
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "freight", "harga_penyerahan",
		"jabatan_pernyataan", "kode_jenis_tpb", "kode_kantor", "kode_lokasi_bayar", "kode_tujuan_pengiriman",
		"kota_pernyataan", "nama_pernyataan", "netto", "nilai_barang", "nomoraju", "ppn_pajak",
		"ppnbm_pajak", "tanggal_pernyataan", "uang_muka", "vd", "volume", "entitas", "kemasan",
		"kontainer", "pengangkut", "dokumen"
	],
	"33": [ // BC33 - FTZ Ekspor
		"asuransi", "bruto", "cif", "flag_curah", "freight", "jabatan_pernyataan", "kode_asuransi",
		"kode_cara_angkut", "kode_cara_bayar", "kode_cara_dagang", "kode_jenis_ekspor",
		"kode_jenis_prosedur", "kode_kantor", "kode_kategori_ekspor", "kode_pelabuhan_bongkar",
		"kode_pelabuhan_muat", "kode_pelabuhan_tujuan", "kode_valuta", "kota_pernyataan",
		"nama_pernyataan", "ndpbm", "netto", "nomoraju", "tanggal_pernyataan", "volume",
		"entitas", "kemasan", "kontainer", "pengangkut", "dokumen"
	],
	"262": [ // BC262 - TPB Keluar ke TLDDP
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "disclaimer", "freight",
		"harga_penyerahan", "jabatan_pernyataan", "kode_kantor", "kode_tujuan_pemasukan",
		"kode_tujuan_pengiriman", "kode_valuta", "kota_pernyataan", "nama_pernyataan", "ndpbm",
		"nilai_barang", "nomoraju", "tanggal_pernyataan", "uang_muka", "vd", "entitas", "kemasan",
		"pengangkut", "dokumen"
	],
	"261": [ // BC261 - TPB Masuk dari TLDDP
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "disclaimer", "freight",
		"harga_penyerahan", "jabatan_pernyataan", "kode_kantor", "kode_tujuan_pengiriman",
		"kode_valuta", "kota_pernyataan", "nama_pernyataan", "ndpbm", "nilai_barang", "nomoraju",
		"tanggal_pernyataan", "uang_muka", "vd", "entitas", "kemasan", "kontainer", "pengangkut", "dokumen"
	],
	"16": [ // BC16 - FTZ Masuk
		"bruto", "cif", "jabatan_pernyataan", "kode_incoterm", "kode_jenis_nilai", "kode_kantor",
		"kode_kantor_bongkar", "kode_pelabuhan_bongkar", "kode_pelabuhan_muat", "kode_pelabuhan_transit",
		"kode_tps", "kode_tutup_pu", "kode_valuta", "kota_pernyataan", "nama_pernyataan", "ndpbm",
		"nomor_bc11", "nomor_pos", "nomor_sub_pos", "nomoraju", "tanggal_bc11", "tanggal_pernyataan",
		"tanggal_tiba", "entitas", "kemasan", "pengangkut", "dokumen"
	],
	"28": [ // BC28 - Impor PLB
		"bruto", "cif", "jabatan_pernyataan", "kode_cara_angkut", "kode_cara_bayar", "kode_incoterm",
		"kode_jenis_impor", "kode_jenis_nilai", "kode_jenis_prosedur", "kode_kantor", "kode_tps",
		"kode_valuta", "kota_pernyataan", "nama_pernyataan", "ndpbm", "nilai_barang", "nomoraju",
		"tanggal_pernyataan", "tanggal_tiba", "volume", "entitas", "kemasan", "dokumen"
	],
	"331": [ // BC331 - P3BET
		"asuransi", "bruto", "cif", "disclaimer", "freight", "jabatan_pernyataan", "jumlah_tanda_pengaman",
		"kode_asuransi", "kode_tps", "kode_tanda_pengaman", "kode_jenis_tanda_pengaman", "kode_kantor",
		"kode_kantor_muat", "kode_negara_tujuan", "kode_pelabuhan_bongkar", "kode_pelabuhan_muat",
		"kode_pelabuhan_tujuan", "kota_pernyataan", "nama_pernyataan", "netto", "nilai_barang", "nomoraju",
		"tanggal_muat", "tanggal_pernyataan", "tempat_stuffing",
		"entitas", "kemasan", "kontainer", "dokumen", "pengangkut"
	],
	"511": [ // FTZ01-1
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "dokumen", "entitas", "fob", "freight",
		"jabatan_pernyataan", "kemasan", "kode_asal_barang_ftz", "kode_asuransi", "kode_cara_bayar",
		"kode_cara_dagang", "kode_incoterm", "kode_jenis_pib", "kode_kantor", "kode_kategori_barang_ftz",
		"kode_kategori_masuk_ftz", "kode_pelabuhan_muat", "kode_pelabuhan_transit", "kode_pelabuhan_tujuan",
		"kode_tps", "kode_tujuan_pemasukan", "kode_tujuan_pengiriman", "kode_tutup_pu", "kode_valuta",
		"kontainer", "kota_pernyataan", "nama_pernyataan", "nama_transaksi_lainnya_ftz", "ndpbm", "netto",
		"nomor_bc11", "nomor_pos", "nomor_sub_pos", "nomoraju", "pengangkut", "tanggal_bc11",
		"tanggal_pernyataan", "tanggal_tiba", "volume"
	],
	"512": [ // FTZ01-2
		"asuransi", "bank_devisa", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "dokumen", "entitas",
		"flag_curah", "fob", "freight", "harga_penyerahan", "jabatan_pernyataan", "jumlah_tanda_pengaman",
		"kemasan", "kode_asal_barang_ftz", "kode_asuransi", "kode_cara_bayar", "kode_cara_dagang",
		"kode_incoterm", "kode_jenis_pib", "kode_kantor", "kode_kategori_keluar_ftz", "kode_negara_tujuan",
		"kode_pelabuhan_muat", "kode_pelabuhan_transit", "kode_pelabuhan_tujuan", "kode_tps",
		"kode_tujuan_pengiriman", "kode_valuta", "kontainer", "kota_pernyataan", "nama_pernyataan", "ndpbm",
		"netto", "nilai_barang", "nilai_incoterm", "nilai_maklon", "nomoraju", "pengangkut",
		"tanggal_berangkat", "tanggal_pernyataan", "total_dana_sawit", "volume"
	],
	"513": [ // FTZ01-3
		"asuransi", "biaya_pengurang", "biaya_tambahan", "bruto", "cif", "dokumen", "entitas", "fob", "freight",
		"jabatan_pernyataan", "kemasan", "kode_asal_barang_ftz", "kode_asuransi", "kode_cara_bayar",
		"kode_cara_dagang", "kode_incoterm", "kode_kantor", "kode_kategori_barang_ftz", "kode_kategori_keluar_ftz",
		"kode_pelabuhan_muat", "kode_pelabuhan_transit", "kode_pelabuhan_tujuan", "kode_tps",
		"kode_tujuan_pengeluaran", "kode_tujuan_pengiriman", "kode_tutup_pu", "kode_valuta",
		"kontainer", "kota_pernyataan", "nama_pernyataan", "nama_transaksi_lainnya_ftz", "ndpbm", "netto",
		"nomor_bc11", "nomor_pos", "nomor_sub_pos", "nomoraju", "pengangkut", "tanggal_bc11",
		"tanggal_pernyataan", "tanggal_tiba", "volume"
	]
};

function toggle_fields_by_schema(frm) {
	const doc_type = frm.doc.kode_dokumen;
	
	// Show all fields if no document type is chosen to prevent blocking user
	if (!doc_type || !SCHEMA_FIELDS[doc_type]) {
		frm.meta.fields.forEach(field => {
			frm.set_df_property(field.fieldname, 'hidden', 0);
		});
		return;
	}

	const allowed_fields = SCHEMA_FIELDS[doc_type];

	// Mapping of child table fieldnames to their respective section breaks
	const child_table_sections = {
		"entitas": "section_break_entitas",
		"komponen_biaya": "section_break_komponen",
		"kemasan": "section_break_kemasan",
		"dokumen": "section_break_dokumen",
		"pengangkut": "section_break_pengangkut",
		"kontainer": "section_break_kontainer",
		"bank_devisa": "section_break_sogf",
		"kesiapan_barang": "section_break_dtiu"
	};

	// Iterate through all fields of the DocType and show/hide
	frm.meta.fields.forEach(field => {
		const fname = field.fieldname;
		const ftype = field.fieldtype;

		// 1. Structural Layout Breaks (Tabs and Columns) should always be active
		if (ftype === 'Tab Break' || ftype === 'Column Break') {
			frm.set_df_property(fname, 'hidden', 0);
			return;
		}

		// 2. Always Visible Fields
		if (ALWAYS_VISIBLE_FIELDS.includes(fname)) {
			frm.set_df_property(fname, 'hidden', 0);
			return;
		}

		// 3. Child Table Section Breaks
		let is_child_section = false;
		for (const [table_field, section_field] of Object.entries(child_table_sections)) {
			if (fname === section_field) {
				const show_section = allowed_fields.includes(table_field);
				frm.set_df_property(fname, 'hidden', show_section ? 0 : 1);
				is_child_section = true;
				break;
			}
		}
		if (is_child_section) return;

		// Generic Section Breaks should remain visible to maintain formatting
		if (ftype === 'Section Break') {
			frm.set_df_property(fname, 'hidden', 0);
			return;
		}

		// 4. Regular fields & child table fields
		const should_show = allowed_fields.includes(fname);
		frm.set_df_property(fname, 'hidden', should_show ? 0 : 1);
	});

	// Always hide asaldata as it is a system/metadata field
	frm.set_df_property('asaldata', 'hidden', 1);
}


frappe.ui.form.on('HEADER V21', {
	onload: function (frm) {
		toggle_fields_by_schema(frm);
	},
	refresh: function (frm) {
		toggle_fields_by_schema(frm);
		frm.clear_custom_buttons();

		// Change background color
		frm.page.wrapper.find('.layout-main-section').css('background-color', '#F3F4F6');

		// Add Barang Manager Button
		if (frm.doc.name) {
			add_beacukai_actions(frm);
			try {
				render_ceisa_pdf_dashboard(frm);
			} catch (err) {
				console.error("Error rendering CEISA PDF Dashboard:", err);
			}
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
														frappe.set_route('Form', 'HEADER V21', r2.message.nomor_aju);
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
	},
	kode_dokumen: function (frm) {
		frm.trigger('refresh');
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

	if (frm.doc.docstatus === 0) {
		frm.add_custom_button(__('📋 Cek Manifest & Kurs'), function () {
			check_manifest_and_kurs(frm);
		}, __('Beacukai')).attr('style', 'background:#00897B;color:#fff;border-color:#00695C;font-weight:600;');
	}

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
function check_manifest_and_kurs(frm) {
	frappe.call({
		method: 'singlecore_apps.singlecore_apps.doctype.header_v21.header_v21.validate_manifest_and_kurs_endpoint',
		args: {
			docname: frm.doc.name
		},
		freeze: true,
		freeze_message: __('Melakukan validasi & sinkronisasi Manifest dan Kurs via CEISA API...'),
		callback: function (r) {
			if (r.message && r.message.status === 'success') {
				frappe.show_alert({
					message: __('Validasi & sinkronisasi sukses! Data manifest & kurs telah diperbarui.'),
					indicator: 'green'
				});
				frm.reload_doc();
			}
		}
	});
}

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

function render_ceisa_pdf_dashboard(frm) {
	const nomor_aju = frm.doc.nomoraju || frm.doc.name;
	if (!nomor_aju) return;

	// Resolve dashboard wrapper element with multiple fallbacks
	let $jq_wrapper = null;
	if (frm.dashboard && (frm.dashboard.wrapper || frm.dashboard.$wrapper)) {
		$jq_wrapper = $(frm.dashboard.wrapper || frm.dashboard.$wrapper);
	} else if (frm.dashboard_area && frm.dashboard_area.length) {
		$jq_wrapper = frm.dashboard_area;
	} else {
		$jq_wrapper = frm.page && frm.page.wrapper ? frm.page.wrapper.find('.form-dashboard') : null;
	}

	if (!$jq_wrapper || !$jq_wrapper.length) {
		console.warn("CEISA Dashboard: Could not find any form dashboard container element.");
		return;
	}

	// Inject styles
	if (!$('#ceisa-dashboard-styles').length) {
		$('<style id="ceisa-dashboard-styles">').prop('type', 'text/css').html(`
			.ceisa-pdf-dashboard {
				background: rgba(255, 255, 255, 0.7);
				backdrop-filter: blur(20px) saturate(190%);
				-webkit-backdrop-filter: blur(20px) saturate(190%);
				border: 1px solid rgba(209, 213, 219, 0.3);
				border-radius: 16px;
				padding: 20px;
				margin: 15px 0 25px 0;
				box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.04);
				font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
				transition: all 0.3s ease;
			}
			.ceisa-pdf-dashboard:hover {
				box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.08);
				border-color: rgba(209, 213, 219, 0.5);
			}
			.ceisa-dashboard-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
				margin-bottom: 16px;
				border-bottom: 1px solid rgba(229, 231, 235, 0.5);
				padding-bottom: 12px;
			}
			.ceisa-dashboard-title {
				font-size: 15px;
				font-weight: 700;
				color: #1F2937;
				display: flex;
				align-items: center;
				gap: 8px;
			}
			.ceisa-dashboard-title i {
				color: #2563EB;
			}
			.ceisa-dashboard-subtitle {
				font-size: 11px;
				color: #6B7280;
				font-weight: 500;
			}
			.ceisa-actions-row {
				display: flex;
				flex-wrap: wrap;
				gap: 12px;
				margin-bottom: 18px;
			}
			.ceisa-btn {
				display: inline-flex;
				align-items: center;
				justify-content: center;
				gap: 8px;
				padding: 10px 18px;
				font-size: 13px;
				font-weight: 600;
				border-radius: 10px;
				cursor: pointer;
				transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
				user-select: none;
				text-decoration: none !important;
			}
			.ceisa-btn-draft {
				background: hsla(210, 60%, 45%, 0.06);
				color: hsla(210, 70%, 35%, 1);
				border: 1px solid hsla(210, 60%, 45%, 0.2);
			}
			.ceisa-btn-draft:hover {
				background: hsla(210, 60%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12);
			}
			.ceisa-btn-final {
				background: hsla(150, 60%, 40%, 0.06);
				color: hsla(150, 65%, 28%, 1);
				border: 1px solid hsla(150, 60%, 40%, 0.2);
			}
			.ceisa-btn-final:hover {
				background: hsla(150, 60%, 40%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 12px rgba(16, 185, 129, 0.12);
			}
			.ceisa-btn-billing {
				background: hsla(35, 85%, 45%, 0.06);
				color: hsla(35, 90%, 30%, 1);
				border: 1px solid hsla(35, 85%, 45%, 0.2);
			}
			.ceisa-btn-billing:hover {
				background: hsla(35, 85%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 12px rgba(245, 158, 11, 0.12);
			}
			.ceisa-btn-check {
				background: hsla(275, 60%, 45%, 0.06);
				color: hsla(275, 70%, 35%, 1);
				border: 1px solid hsla(275, 60%, 45%, 0.2);
			}
			.ceisa-btn-check:hover {
				background: hsla(275, 60%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 12px rgba(139, 92, 246, 0.12);
			}
			.ceisa-btn-upload {
				background: hsla(200, 75%, 45%, 0.06);
				color: hsla(200, 80%, 32%, 1);
				border: 1px solid hsla(200, 75%, 45%, 0.2);
			}
			.ceisa-btn-upload:hover {
				background: hsla(200, 75%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 12px rgba(14, 165, 233, 0.12);
			}
			.ceisa-btn:active {
				transform: translateY(0);
			}
			.ceisa-spinner {
				width: 13px;
				height: 13px;
				border: 2px solid currentColor;
				border-top-color: transparent;
				border-radius: 50%;
				animation: ceisa-spin 0.7s linear infinite;
				display: inline-block;
			}
			@keyframes ceisa-spin {
				to { transform: rotate(360deg); }
			}
			.ceisa-response-section {
				border-top: 1px dashed rgba(209, 213, 219, 0.5);
				padding-top: 16px;
			}
			.ceisa-response-section-title {
				font-size: 11px;
				font-weight: 700;
				color: #4B5563;
				margin-bottom: 12px;
				text-transform: uppercase;
				letter-spacing: 0.05em;
				display: flex;
				align-items: center;
				gap: 6px;
			}
			.ceisa-response-grid {
				display: flex;
				flex-wrap: wrap;
				gap: 8px;
			}
			.ceisa-pill {
				display: inline-flex;
				align-items: center;
				gap: 6px;
				padding: 6px 14px;
				font-size: 11.5px;
				font-weight: 600;
				border-radius: 20px;
				cursor: pointer;
				transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
				user-select: none;
			}
			.ceisa-pill-success {
				background: hsla(150, 60%, 45%, 0.05);
				color: hsla(150, 70%, 28%, 1);
				border: 1px solid hsla(150, 60%, 45%, 0.15);
			}
			.ceisa-pill-success:hover {
				background: hsla(150, 60%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 10px rgba(16, 185, 129, 0.1);
			}
			.ceisa-pill-action {
				background: hsla(5, 75%, 45%, 0.05);
				color: hsla(5, 80%, 35%, 1);
				border: 1px solid hsla(5, 75%, 45%, 0.15);
			}
			.ceisa-pill-action:hover {
				background: hsla(5, 75%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 10px rgba(239, 68, 68, 0.1);
			}
			.ceisa-pill-info {
				background: hsla(200, 65%, 45%, 0.05);
				color: hsla(200, 75%, 32%, 1);
				border: 1px solid hsla(200, 65%, 45%, 0.15);
			}
			.ceisa-pill-info:hover {
				background: hsla(200, 65%, 45%, 0.12);
				transform: translateY(-2px);
				box-shadow: 0 4px 10px rgba(59, 130, 246, 0.1);
			}
			.ceisa-pill-cached {
				border-style: solid;
				border-width: 1.5px;
				background: rgba(255, 255, 255, 0.85) !important;
			}
			.ceisa-pill-cached.ceisa-pill-success {
				border-color: hsla(150, 60%, 45%, 0.45);
			}
			.ceisa-pill-cached.ceisa-pill-action {
				border-color: hsla(5, 75%, 45%, 0.45);
			}
			.ceisa-pill-cached.ceisa-pill-info {
				border-color: hsla(200, 65%, 45%, 0.45);
			}
			.ceisa-pill-cached-badge {
				font-size: 9px;
				margin-left: 2px;
				color: hsla(150, 70%, 28%, 0.8);
			}
		`).appendTo('head');
	}

	// Ensure the dashboard wrapper container is visible
	$jq_wrapper.show();
	if (frm.dashboard && typeof frm.dashboard.show === 'function') {
		try {
			frm.dashboard.show();
		} catch (e) {
			console.warn("Could not call frm.dashboard.show():", e);
		}
	}

	// Remove old wrapper if it exists to prevent duplication on multiple refreshes
	$jq_wrapper.find('.ceisa-pdf-dashboard').remove();

	// Construct the premium dashboard card
	const html = `
		<div class="ceisa-pdf-dashboard">
			<div class="ceisa-dashboard-header">
				<div class="ceisa-dashboard-title">
					<i class="fa fa-cloud-download"></i> 
					<span>CEISA 4.0 PDF Workspace</span>
				</div>
				<div class="ceisa-dashboard-subtitle">Nomor Aju: ${nomor_aju}</div>
			</div>
			
			<div class="ceisa-actions-row">
				<div class="ceisa-btn ceisa-btn-draft" id="ceisa-btn-draft" data-nomor-aju="${nomor_aju}">
					<i class="fa fa-file-text-o"></i> <span>Draft Formulir</span>
				</div>
				<div class="ceisa-btn ceisa-btn-final" id="ceisa-btn-final" data-nomor-aju="${nomor_aju}">
					<i class="fa fa-file-pdf-o"></i> <span>Final Formulir</span>
				</div>
				<div class="ceisa-btn ceisa-btn-billing" id="ceisa-btn-billing" data-nomor-aju="${nomor_aju}">
					<i class="fa fa-credit-card"></i> <span>Billing PDF</span>
				</div>
				<div class="ceisa-btn ceisa-btn-check" id="ceisa-btn-check" data-nomor-aju="${nomor_aju}">
					<i class="fa fa-refresh"></i> <span>Cek Status CEISA</span>
				</div>
				<div class="ceisa-btn ceisa-btn-upload" id="ceisa-btn-upload" data-nomor-aju="${nomor_aju}">
					<i class="fa fa-upload"></i> <span>Upload Dok-Pelengkap</span>
				</div>
			</div>
			
			<div class="ceisa-response-section" style="display: none;">
				<div class="ceisa-response-section-title">
					<i class="fa fa-tags"></i> <span>Daftar Respon Kepabeanan</span>
				</div>
				<div class="ceisa-response-grid" id="ceisa-response-grid">
					<!-- Pills will be dynamically loaded here -->
				</div>
			</div>
		</div>
	`;

	// Append to dashboard wrapper
	$jq_wrapper.prepend(html);

	const wrapper = $jq_wrapper.find('.ceisa-pdf-dashboard');
	setup_ceisa_dashboard_actions(frm, wrapper);
	load_ceisa_response_pills(frm, wrapper);
}

function setup_ceisa_dashboard_actions(frm, wrapper) {
	const nomor_aju = frm.doc.nomoraju || frm.doc.name;

	// 1. DRAFT FORMULIR
	wrapper.find('#ceisa-btn-draft').on('click', function() {
		const $btn = $(this);
		if ($btn.hasClass('disabled')) return;
		
		$btn.addClass('disabled').find('i').removeClass('fa-file-text-o').addClass('ceisa-spinner');
		
		frappe.call({
			method: 'singlecore_apps.api.ceisa_api.status.get_cetak_formulir_draft',
			args: { nomor_aju: nomor_aju },
			callback: function(r) {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-file-text-o');
				if (r.message && r.message.status === 'success') {
					window.open(r.message.data, '_blank');
				} else {
					frappe.msgprint({
						title: 'Gagal Mengunduh Draft',
						message: r.message ? r.message.message : 'Terjadi kesalahan sistem saat menghubungi CEISA.',
						indicator: 'red'
					});
				}
			},
			error: function() {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-file-text-o');
			}
		});
	});

	// 2. FINAL FORMULIR
	wrapper.find('#ceisa-btn-final').on('click', function() {
		const $btn = $(this);
		if ($btn.hasClass('disabled')) return;
		
		$btn.addClass('disabled').find('i').removeClass('fa-file-pdf-o').addClass('ceisa-spinner');
		
		frappe.call({
			method: 'singlecore_apps.api.ceisa_api.status.get_cetak_formulir_final',
			args: { nomor_aju: nomor_aju },
			callback: function(r) {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-file-pdf-o');
				if (r.message && r.message.status === 'success') {
					window.open(r.message.data, '_blank');
				} else {
					frappe.msgprint({
						title: 'Gagal Mengunduh Final',
						message: r.message ? r.message.message : 'Terjadi kesalahan sistem saat menghubungi CEISA.',
						indicator: 'red'
					});
				}
			},
			error: function() {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-file-pdf-o');
			}
		});
	});

	// 3. BILLING PDF WITH AUTO SCAN & VERIFICATION DIALOG
	wrapper.find('#ceisa-btn-billing').on('click', function() {
		const $btn = $(this);
		if ($btn.hasClass('disabled')) return;
		
		$btn.addClass('disabled').find('i').removeClass('fa-credit-card').addClass('ceisa-spinner');
		
		frappe.call({
			method: 'singlecore_apps.api.ceisa_api.status.get_active_billing_code',
			args: { nomor_aju: nomor_aju },
			callback: function(r) {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-credit-card');
				if (r.message && r.message.status === 'success') {
					const detected_code = r.message.billing_code;
					
					// Show premium verification dialog
					let d = new frappe.ui.Dialog({
						title: 'Verifikasi Kode Billing CEISA',
						fields: [
							{
								label: 'Nomor Aju',
								fieldname: 'nomor_aju',
								fieldtype: 'Data',
								default: nomor_aju,
								read_only: 1
							},
							{
								label: 'Kode Billing (15 Digit)',
								fieldname: 'billing_code',
								fieldtype: 'Data',
								default: detected_code || '',
								reqd: 1,
								description: detected_code ? 
									'<span style="color: #10B981; font-weight: 600;"><i class="fa fa-check-circle"></i> Kode billing terdeteksi otomatis dari respon CEISA.</span>' : 
									'<span style="color: #F59E0B; font-weight: 600;"><i class="fa fa-warning"></i> Kode billing tidak terdeteksi. Silakan ketik manual.</span>'
							}
						],
						primary_action_label: 'Download Billing PDF',
						primary_action: function(values) {
							let code = (values.billing_code || '').trim();
							if (code.length !== 15 || !/^\d+$/.test(code)) {
								frappe.msgprint({
									title: 'Validasi Gagal',
									message: 'Kode billing harus terdiri dari tepat 15 digit angka.',
									indicator: 'orange'
								});
								return;
							}
							d.hide();
							
							// Trigger billing download with loading spinner state on the dialog trigger
							$btn.addClass('disabled').find('i').removeClass('fa-credit-card').addClass('ceisa-spinner');
							
							frappe.call({
								method: 'singlecore_apps.api.ceisa_api.status.get_billing_pdf',
								args: { nomor_aju: nomor_aju, billing_code: code },
								callback: function(res) {
									$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-credit-card');
									if (res.message && res.message.status === 'success') {
										window.open(res.message.data, '_blank');
									} else {
										frappe.msgprint({
											title: 'Gagal Mengunduh Billing',
											message: res.message ? res.message.message : 'Terjadi kesalahan saat mengunduh PDF Billing.',
											indicator: 'red'
										});
									}
								},
								error: function() {
									$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-credit-card');
								}
							});
						}
					});
					d.show();
				} else {
					frappe.msgprint({
						title: 'Error Pemindaian',
						message: 'Gagal memindai log respon untuk kode billing.',
						indicator: 'red'
					});
				}
			},
			error: function() {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-credit-card');
			}
		});
	});

	// 4. CEK STATUS CEISA
	wrapper.find('#ceisa-btn-check').on('click', function() {
		const $btn = $(this);
		if ($btn.hasClass('disabled')) return;
		
		$btn.addClass('disabled').find('i').removeClass('fa-refresh').addClass('ceisa-spinner');
		
		frappe.call({
			method: 'singlecore_apps.api.check_ceisa_status',
			args: { nomor_aju: nomor_aju },
			callback: function(r) {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-refresh');
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({
						message: __('Status CEISA berhasil disinkronisasi.'),
						indicator: 'green'
					});
					frm.reload_doc();
				} else {
					frappe.msgprint({
						title: 'Gagal Cek Status',
						message: r.message ? (r.message.message || JSON.stringify(r.message)) : 'Terjadi kesalahan sistem saat menghubungi CEISA.',
						indicator: 'red'
					});
				}
			},
			error: function() {
				$btn.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-refresh');
			}
		});
	});

	// 5. UPLOAD DOKUMEN PELENGKAP (NAVIGASI KE TAB DATA 4)
	wrapper.find('#ceisa-btn-upload').on('click', function() {
		if (!frm.scroll_to_field('dokumen')) {
			if (!frm.scroll_to_field('kemasan')) {
				frm.scroll_to_field('data_4_tab');
			}
		}
	});
}

function load_ceisa_response_pills(frm, wrapper) {
	const nomor_aju = frm.doc.nomoraju || frm.doc.name;
	const $grid = wrapper.find('#ceisa-response-grid');
	const $section = wrapper.find('.ceisa-response-section');

	frappe.call({
		method: 'singlecore_apps.api.ceisa_api.status.get_active_responses',
		args: { nomor_aju: nomor_aju },
		callback: function(r) {
			if (r.message && r.message.status === 'success' && r.message.data && r.message.data.length > 0) {
				$grid.empty();
				
				// Show the response section as we have responses
				$section.show();
				
				r.message.data.forEach(function(resp) {
					const code = resp.kode_respon || 'RESPON';
					const is_cached = resp.is_cached === 1;
					const date_str = resp.tanggal_respon ? ` (${resp.tanggal_respon})` : '';
					
					// Determine pill style based on response code status category
					let category_class = 'ceisa-pill-info';
					if (['SPPB', 'NPE'].includes(code.toUpperCase())) {
						category_class = 'ceisa-pill-success';
					} else if (['NPD', 'SPJM', 'TOLAK'].includes(code.toUpperCase())) {
						category_class = 'ceisa-pill-action';
					}
					
					const cached_class = is_cached ? 'ceisa-pill-cached' : '';
					const checkmark = is_cached ? '<span class="ceisa-pill-cached-badge"><i class="fa fa-check-circle"></i></span>' : '';
					
					const tooltip = resp.keterangan ? `${code}: ${resp.keterangan}${date_str}` : `${code}${date_str}`;
					
					const pill_html = `
						<div class="ceisa-pill ${category_class} ${cached_class}" 
							 data-code="${code}" 
							 data-cached="${is_cached ? '1' : '0'}"
							 title="${tooltip}">
							<i class="fa fa-file-text-o"></i>
							<span>${code}</span>
							${checkmark}
						</div>
					`;
					
					const $pill = $(pill_html);
					
					// Handle click on response pill
					$pill.on('click', function() {
						const $this = $(this);
						if ($this.hasClass('disabled')) return;
						
						$this.addClass('disabled').find('i').removeClass('fa-file-text-o').addClass('ceisa-spinner');
						
						frappe.call({
							method: 'singlecore_apps.api.ceisa_api.status.get_response_pdf',
							args: { nomor_aju: nomor_aju, kode_respon: code },
							callback: function(res) {
								$this.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-file-text-o');
								if (res.message && res.message.status === 'success') {
									window.open(res.message.data, '_blank');
									// Make pill cached on successful download if not already cached
									if (!$this.hasClass('ceisa-pill-cached')) {
										$this.addClass('ceisa-pill-cached');
										if (!$this.find('.ceisa-pill-cached-badge').length) {
											$this.append('<span class="ceisa-pill-cached-badge"><i class="fa fa-check-circle"></i></span>');
										}
									}
								} else {
									frappe.msgprint({
										title: `Gagal Mengunduh ${code}`,
										message: res.message ? res.message.message : 'Terjadi kesalahan sistem saat menghubungi CEISA.',
										indicator: 'red'
									});
								}
							},
							error: function() {
								$this.removeClass('disabled').find('i').removeClass('ceisa-spinner').addClass('fa-file-text-o');
							}
						});
					});
					
					$grid.append($pill);
				});
			} else {
				$section.hide();
			}
		}
	});
}

