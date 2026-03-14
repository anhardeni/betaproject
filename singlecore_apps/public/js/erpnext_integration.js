/**
 * ERPNext Integration for Singlecore Apps
 * =========================================
 * Buttons for PO/PI ↔ HEADER V21 integration
 * 
 * Added via hooks.py doctype_js - NO ERPNext core modification
 * 100% safe from ERPNext updates
 */

// ═══════════════════════════════════════════════════════════════════
// BC TYPE OPTIONS (Shared)
// ═══════════════════════════════════════════════════════════════════
const BC_TYPE_OPTIONS = [
    { value: "20", label: "BC 20 - PIB (Pemberitahuan Impor Barang)" },
    { value: "23", label: "BC 23 - TPB Import" },
    { value: "16", label: "BC 16 - Pemasukkan Barang ke PLB" },
    { value: "27", label: "BC 27 - TPB Release" },
    { value: "30", label: "BC 30 - PEB (Pemberitahuan Ekspor Barang)" },
    { value: "33", label: "BC 33 - PLB" },
    { value: "40", label: "BC 40 - TPB from TLDDP" },
    { value: "41", label: "BC 41 - TPB to TLDDP" },
];

function get_bc_options_string() {
    return BC_TYPE_OPTIONS.map(opt => opt.value).join("\n");
}

// ═══════════════════════════════════════════════════════════════════
// SIDE 1: PURCHASE ORDER - Button to create HEADER V21
// ═══════════════════════════════════════════════════════════════════
frappe.ui.form.on("Purchase Order", {
    refresh(frm) {
        // Only show button for submitted PO
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("🚀 Buat HEADER V21"), function () {
                show_create_header_dialog(frm, "po");
            }, __("CEISA"));
        }
    }
});

// ═══════════════════════════════════════════════════════════════════
// SIDE 1: PURCHASE INVOICE - Button to create HEADER V21
// ═══════════════════════════════════════════════════════════════════
frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        // Only show button for submitted PI
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("🚀 Buat HEADER V21"), function () {
                show_create_header_dialog(frm, "pi");
            }, __("CEISA"));
        }
    }
});

// ═══════════════════════════════════════════════════════════════════
// SIDE 2: HEADER V21 - Buttons to import from PO/PI
// ═══════════════════════════════════════════════════════════════════
frappe.ui.form.on("HEADER V21", {
    refresh(frm) {
        // Show Import Data buttons always (even on new documents)

        // Import from single PO
        frm.add_custom_button(__("🔗 Import Purchase Order"), function () {
            ensure_saved_then(frm, () => show_po_picker_dialog(frm));
        }, __("Import Purchase/Delivery Note"));

        // Import from single PI
        frm.add_custom_button(__("📋 Import Purchase Invoice"), function () {
            ensure_saved_then(frm, () => show_pi_picker_dialog(frm));
        }, __("Import Purchase/Delivery Note"));

        // Multi-source import
        frm.add_custom_button(__("📦 Multi-Source PO/PI"), function () {
            ensure_saved_then(frm, () => show_multi_source_dialog(frm));
        }, __("Import Purchase/Delivery Note"));

        // 📥 Import Delivery Note
        frm.add_custom_button(__('📥 Import Delivery Note'), function () {
            show_dn_picker(frm);
        }, __('Import Purchase/Delivery Note')).attr('style', 'background: linear-gradient(135deg, #00B4DB 0%, #0083B0 100%); color: #fff; border: none; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.2); box-shadow: 0 4px 6px rgba(0,180,219,0.2);');
    }
});

// Helper: Ensure document is saved before performing action
function ensure_saved_then(frm, callback) {
    if (frm.is_new() || frm.is_dirty()) {
        frappe.confirm(
            __("Dokumen harus disimpan terlebih dahulu. Simpan sekarang?"),
            function () {
                frm.save().then(() => {
                    callback();
                });
            }
        );
    } else {
        callback();
    }
}


// ═══════════════════════════════════════════════════════════════════
// DIALOG: Create HEADER from PO/PI (used from PO/PI form)
// ═══════════════════════════════════════════════════════════════════
function show_create_header_dialog(frm, source_type) {
    let source_label = source_type === "po" ? "Purchase Order" : "Purchase Invoice";

    let d = new frappe.ui.Dialog({
        title: __("Buat HEADER V21 dari {0}", [source_label]),
        fields: [
            {
                fieldname: "source_info",
                fieldtype: "HTML",
                options: `
                    <div class="alert alert-info">
                        <strong>Sumber:</strong> ${frm.doc.name}<br>
                        <strong>Supplier:</strong> ${frm.doc.supplier_name || frm.doc.supplier}<br>
                        <strong>Total:</strong> ${format_currency(frm.doc.grand_total, frm.doc.currency)}<br>
                        <strong>Items:</strong> ${frm.doc.items ? frm.doc.items.length : 0} barang
                    </div>
                `
            },
            {
                fieldname: "kode_dokumen",
                fieldtype: "Select",
                label: __("Jenis Dokumen BC"),
                options: get_bc_options_string(),
                default: "23",
                reqd: 1,
                description: "Pilih jenis dokumen BC yang akan dibuat"
            }
        ],
        size: "small",
        primary_action_label: __("Buat HEADER V21"),
        primary_action(values) {
            d.hide();

            frappe.call({
                method: source_type === "po"
                    ? "singlecore_apps.api.po_pi_integration.make_header_v21_from_po"
                    : "singlecore_apps.api.po_pi_integration.make_header_v21_from_pi",
                args: {
                    [source_type === "po" ? "po_name" : "pi_name"]: frm.doc.name,
                    kode_dokumen: values.kode_dokumen
                },
                freeze: true,
                freeze_message: __("Membuat HEADER V21..."),
                callback: function (r) {
                    if (r.message) {
                        if (r.message.status === "success") {
                            frappe.msgprint({
                                title: __("Berhasil"),
                                message: `
                                    ✅ HEADER V21 berhasil dibuat!<br><br>
                                    <strong>Nomor:</strong> ${r.message.header_name}<br>
                                    <strong>Nomor Aju:</strong> ${r.message.nomor_aju}<br>
                                    <strong>Barang:</strong> ${r.message.barang_count} items<br>
                                    <strong>Total CIF:</strong> ${format_currency(r.message.total_value, frm.doc.currency)}
                                `,
                                indicator: "green",
                                primary_action: {
                                    label: __("Buka HEADER V21"),
                                    action: function () {
                                        frappe.set_route("Form", "HEADER V21", r.message.header_name);
                                    }
                                }
                            });
                        } else {
                            frappe.msgprint({
                                title: __("Error"),
                                message: r.message.message,
                                indicator: "red"
                            });
                        }
                    }
                }
            });
        }
    });
    d.show();
}


// ═══════════════════════════════════════════════════════════════════
// DIALOG: Pick PO to import (used from HEADER V21 form)
// ═══════════════════════════════════════════════════════════════════
function show_po_picker_dialog(frm) {
    // Fetch available POs first
    frappe.call({
        method: "singlecore_apps.api.po_pi_integration.get_available_purchase_orders",
        callback: function (r) {
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__("Tidak ada Purchase Order yang sudah di-submit"));
                return;
            }

            let po_options = r.message.map(po => ({
                label: `${po.name} - ${po.supplier_name} (${format_currency(po.grand_total, po.currency)})`,
                value: po.name
            }));

            let d = new frappe.ui.Dialog({
                title: __("Import dari Purchase Order"),
                fields: [
                    {
                        fieldname: "po_name",
                        fieldtype: "Autocomplete",
                        label: __("Pilih Purchase Order"),
                        options: po_options.map(o => o.value),
                        reqd: 1
                    }
                ],
                primary_action_label: __("Import"),
                primary_action(values) {
                    d.hide();

                    frappe.call({
                        method: "singlecore_apps.api.po_pi_integration.populate_header_from_po",
                        args: {
                            header_name: frm.doc.name,
                            po_name: values.po_name
                        },
                        freeze: true,
                        freeze_message: __("Importing data..."),
                        callback: function (r) {
                            handle_import_response(r, frm);
                        }
                    });
                }
            });
            d.show();
        }
    });
}


// ═══════════════════════════════════════════════════════════════════
// DIALOG: Pick PI to import (used from HEADER V21 form)
// ═══════════════════════════════════════════════════════════════════
function show_pi_picker_dialog(frm) {
    frappe.call({
        method: "singlecore_apps.api.po_pi_integration.get_available_purchase_invoices",
        callback: function (r) {
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__("Tidak ada Purchase Invoice yang sudah di-submit"));
                return;
            }

            let pi_options = r.message.map(pi => ({
                label: `${pi.name} - ${pi.supplier_name} (${format_currency(pi.grand_total, pi.currency)})`,
                value: pi.name
            }));

            let d = new frappe.ui.Dialog({
                title: __("Import dari Purchase Invoice"),
                fields: [
                    {
                        fieldname: "pi_name",
                        fieldtype: "Autocomplete",
                        label: __("Pilih Purchase Invoice"),
                        options: pi_options.map(o => o.value),
                        reqd: 1
                    }
                ],
                primary_action_label: __("Import"),
                primary_action(values) {
                    d.hide();

                    frappe.call({
                        method: "singlecore_apps.api.po_pi_integration.populate_header_from_pi",
                        args: {
                            header_name: frm.doc.name,
                            pi_name: values.pi_name
                        },
                        freeze: true,
                        freeze_message: __("Importing data..."),
                        callback: function (r) {
                            handle_import_response(r, frm);
                        }
                    });
                }
            });
            d.show();
        }
    });
}


// ═══════════════════════════════════════════════════════════════════
// DIALOG: Multi-source import (used from HEADER V21 form)
// ═══════════════════════════════════════════════════════════════════
function show_multi_source_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __("Import dari Multiple PO/PI"),
        fields: [
            {
                fieldname: "source_type",
                fieldtype: "Select",
                label: __("Jenis Sumber"),
                options: "Purchase Order\nPurchase Invoice",
                default: "Purchase Order",
                reqd: 1
            },
            {
                fieldname: "sources",
                fieldtype: "Small Text",
                label: __("Nomor Dokumen"),
                description: "Masukkan nomor dokumen, pisahkan dengan koma. Contoh: PO-001, PO-002",
                reqd: 1
            }
        ],
        primary_action_label: __("Import All"),
        primary_action(values) {
            let sources = values.sources.split(",").map(s => s.trim()).filter(s => s);
            let source_type = values.source_type === "Purchase Order" ? "po" : "pi";

            if (sources.length === 0) {
                frappe.msgprint(__("Masukkan minimal satu nomor dokumen"));
                return;
            }

            d.hide();

            // Import all sources sequentially
            let imported = 0;
            let errors = [];
            let total = sources.length;

            function importNext(index) {
                if (index >= sources.length) {
                    // All done - show summary
                    let summary = `✅ ${imported} dari ${total} dokumen berhasil diimport.`;
                    if (errors.length > 0) {
                        summary += `<br><br>❌ Gagal:<br>` + errors.join("<br>");
                    }
                    frappe.msgprint({
                        title: __("Multi-Import Selesai"),
                        message: summary,
                        indicator: errors.length > 0 ? "orange" : "green",
                        wide: true
                    });
                    frm.reload_doc();
                    return;
                }

                let current_source = sources[index];
                frappe.call({
                    method: source_type === "po"
                        ? "singlecore_apps.api.po_pi_integration.populate_header_from_po"
                        : "singlecore_apps.api.po_pi_integration.populate_header_from_pi",
                    args: {
                        header_name: frm.doc.name,
                        [source_type === "po" ? "po_name" : "pi_name"]: current_source
                    },
                    freeze: true,
                    freeze_message: __("Importing {0} of {1}: {2}...", [index + 1, total, current_source]),
                    callback: function (r) {
                        if (r.message && r.message.status === "success") {
                            imported++;
                        } else {
                            errors.push(`${current_source}: ${r.message ? r.message.message : "Unknown error"}`);
                        }
                        // Import next one
                        importNext(index + 1);
                    },
                    error: function (err) {
                        errors.push(`${current_source}: ${err.message || "Request failed"}`);
                        importNext(index + 1);
                    }
                });
            }

            // Start importing from first document
            importNext(0);
        }
    });
    d.show();
}


// ═══════════════════════════════════════════════════════════════════
// HELPER: Handle import response
// ═══════════════════════════════════════════════════════════════════
function handle_import_response(r, frm) {
    if (r.message) {
        if (r.message.status === "success") {
            frappe.show_alert({
                message: r.message.message,
                indicator: "green"
            }, 5);
            frm.reload_doc();
        } else {
            frappe.msgprint({
                title: __("Error"),
                message: r.message.message,
                indicator: "red"
            });
        }
    }
}

/**
 * 🌊 AMBIENT DN PICKER
 * Immersive UI to pull data from Delivery Notes
 */
function show_dn_picker(frm) {
    let d = new frappe.ui.Dialog({
        title: '<div style="background: linear-gradient(90deg, #00B4DB 0%, #0083B0 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 1.25em;">🌊 Immersive DN Import</div>',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'intro',
                options: `
 					<div style="padding: 15px; background: rgba(0, 180, 219, 0.05); border-radius: 12px; border: 1px solid rgba(0, 180, 219, 0.1); margin-bottom: 20px;">
 						<p style="margin: 0; color: #00796B; font-weight: 500;">Pilih Delivery Note dari list di bawah untuk melakukan sinkronisasi data ke <b>HEADER V21</b> ini secara cerdas.</p>
 					</div>
 				`
            },
            {
                label: 'Select Delivery Note',
                fieldname: 'dn_name',
                fieldtype: 'Link',
                options: 'Delivery Note',
                reqd: 1,
                get_query: () => {
                    return { filters: { docstatus: 1 } };
                },
                description: 'Hanya DN yang sudah di-Submit yang akan muncul.'
            },
            {
                label: 'Price List (Optional)',
                fieldname: 'price_list',
                fieldtype: 'Link',
                options: 'Price List',
                description: 'Digunakan jika rate di DN/SO/SI kosong.'
            },
            {
                label: 'Advanced Settings',
                fieldtype: 'Section Break',
                collapsible: 1
            },
            {
                label: 'Kode Dokumen Sumber (DOKUMEN)',
                fieldname: 'kode_dokumen_sumber',
                fieldtype: 'Data',
                default: '999',
                description: 'Kode CEISA untuk dokumen DN (default 999).'
            },
            {
                label: 'Mode Import',
                fieldname: 'mode',
                fieldtype: 'Select',
                options: [
                    { label: 'Replace / New (Create New Header)', value: 'new' },
                    { label: 'Append to Current Header', value: 'append' }
                ],
                default: 'append',
            }
        ],
        primary_action_label: '✨ Sync Now',
        primary_action: function (values) {
            const method = values.mode === 'new' ?
                'singlecore_apps.api.dn_so_si_integration.make_header_v21_from_dn' :
                'singlecore_apps.api.dn_so_si_integration.populate_header_from_dn';

            const args = {
                dn_name: values.dn_name,
                price_list: values.price_list,
                kode_dokumen_sumber_dn: values.kode_dokumen_sumber
            };

            if (values.mode === 'append') {
                args.header_name = frm.doc.name;
            }

            d.hide();

            frappe.call({
                method: method,
                args: args,
                freeze: true,
                freeze_message: '🌊 Synchronizing Ambient Data...',
                callback: function (r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint({
                            title: '<span style="color: #0083B0;">✨ Synchronization Successful</span>',
                            message: r.message.message,
                            indicator: 'green',
                            wide: true
                        });
                        if (values.mode === 'new') {
                            frappe.set_route('Form', 'HEADER V21', r.message.header_name);
                        } else {
                            frm.reload_doc();
                        }
                    } else {
                        frappe.msgprint({
                            title: '❌ Sync Failed',
                            message: (r.message ? r.message.message : 'Unknown error'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });

    d.show();

    // Inject some ambient CSS to the dialog
    d.$wrapper.find('.modal-content').css({
        'border-radius': '20px',
        'overflow': 'hidden',
        'box-shadow': '0 20px 50px rgba(0, 180, 219, 0.15)',
        'border': '1px solid rgba(0, 180, 219, 0.1)'
    });
    d.$wrapper.find('.primary-action').css({
        'background': 'linear-gradient(135deg, #00B4DB 0%, #0083B0 100%)',
        'border': 'none',
        'border-radius': '8px',
        'padding': '8px 20px',
        'font-weight': '700',
        'box-shadow': '0 4px 15px rgba(0, 131, 176, 0.3)'
    });
}
