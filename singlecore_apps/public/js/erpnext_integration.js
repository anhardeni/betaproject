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
    { value: "20", label: "BC 2.0 - PIB (Pemberitahuan Impor Barang)" },
    { value: "23", label: "BC 2.3 - TPB Import" },
    { value: "25", label: "BC 2.5 - TPB Internal Transfer" },
    { value: "27", label: "BC 2.7 - TPB Release" },
    { value: "30", label: "BC 3.0 - PEB (Pemberitahuan Ekspor Barang)" },
    { value: "33", label: "BC 3.3 - PLB" },
    { value: "40", label: "BC 4.0 - TPB from TLDDP" },
    { value: "41", label: "BC 4.1 - TPB to TLDDP" },
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
        frm.add_custom_button(__("🔗 Import dari PO"), function () {
            ensure_saved_then(frm, () => show_po_picker_dialog(frm));
        }, __("Import Data"));

        // Import from single PI
        frm.add_custom_button(__("📋 Import dari PI"), function () {
            ensure_saved_then(frm, () => show_pi_picker_dialog(frm));
        }, __("Import Data"));

        // Multi-source import
        frm.add_custom_button(__("📦 Multi-Source Import"), function () {
            ensure_saved_then(frm, () => show_multi_source_dialog(frm));
        }, __("Import Data"));
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
