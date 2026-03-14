/**
 * ERPNext Export Integration for Singlecore Apps
 * ================================================
 * Buttons for SO/SI ↔ HEADER V21 integration (Export documents: BC25, BC27, BC30, BC33)
 * 
 * Added via hooks.py doctype_js - NO ERPNext core modification
 * 100% safe from ERPNext updates
 */

// ═══════════════════════════════════════════════════════════════════
// BC TYPE OPTIONS (Export only)
// ═══════════════════════════════════════════════════════════════════
const BC_EXPORT_OPTIONS = [
    { value: "25", label: "BC 2.5 - TPB Internal Transfer" },
    { value: "27", label: "BC 2.7 - TPB Release" },
    { value: "28", label: "BC 2.8 - Pengeluaran Barang dari PLB" },
    { value: "30", label: "BC 3.0 - PEB (Pemberitahuan Ekspor Barang)" },
    { value: "33", label: "BC 3.3 - PLB" },
];

function get_bc_export_options_string() {
    return BC_EXPORT_OPTIONS.map(opt => opt.value).join("\n");
}

// ═══════════════════════════════════════════════════════════════════
// SIDE 1: SALES ORDER - Button to create HEADER V21
// ═══════════════════════════════════════════════════════════════════
frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        // Only show button for submitted SO
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("🚀 Buat HEADER V21"), function () {
                show_create_header_dialog(frm, "so");
            }, __("CEISA"));
        }
    }
});

// ═══════════════════════════════════════════════════════════════════
// SIDE 1: SALES INVOICE - Button to create HEADER V21
// ═══════════════════════════════════════════════════════════════════
frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        // Only show button for submitted SI
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("🚀 Buat HEADER V21"), function () {
                show_create_header_dialog(frm, "si");
            }, __("CEISA"));
        }
    }
});

// ═══════════════════════════════════════════════════════════════════
// SIDE 2: HEADER V21 - Buttons to import from SO/SI (Export)
// ═══════════════════════════════════════════════════════════════════
frappe.ui.form.on("HEADER V21", {
    refresh(frm) {
        // Check if this is an export document type
        let export_codes = ["25", "27", "28", "30", "33"];
        let is_export = export_codes.includes(frm.doc.kode_dokumen);

        // Show Export import buttons
        if (is_export || !frm.doc.kode_dokumen) {
            // Import from single SO
            frm.add_custom_button(__("📦 Import Sales Order"), function () {
                ensure_saved_then(frm, () => show_so_picker_dialog(frm));
            }, __("Import from Sales Document"));

            // Import from single SI
            frm.add_custom_button(__("🧾 Import Sales Invoice"), function () {
                ensure_saved_then(frm, () => show_si_picker_dialog(frm));
            }, __("Import from Sales Document"));

            // Multi-source import for export
            frm.add_custom_button(__("📦 Multi-Source SO/SI"), function () {
                ensure_saved_then(frm, () => show_multi_source_export_dialog(frm));
            }, __("Import from Sales Document"));
        }
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
// DIALOG: Create HEADER from SO/SI (used from SO/SI form)
// ═══════════════════════════════════════════════════════════════════
function show_create_header_dialog(frm, source_type) {
    let source_label = source_type === "so" ? "Sales Order" : "Sales Invoice";

    let d = new frappe.ui.Dialog({
        title: __("Buat HEADER V21 dari {0}", [source_label]),
        fields: [
            {
                fieldname: "source_info",
                fieldtype: "HTML",
                options: `
                    <div class="alert alert-info">
                        <strong>Sumber:</strong> ${frm.doc.name}<br>
                        <strong>Customer:</strong> ${frm.doc.customer_name || frm.doc.customer}<br>
                        <strong>Total:</strong> ${format_currency(frm.doc.grand_total, frm.doc.currency)}<br>
                        <strong>Items:</strong> ${frm.doc.items ? frm.doc.items.length : 0} barang
                    </div>
                `
            },
            {
                fieldname: "kode_dokumen",
                fieldtype: "Select",
                label: __("Jenis Dokumen BC"),
                options: get_bc_export_options_string(),
                default: "30",
                reqd: 1,
                description: "Pilih jenis dokumen BC ekspor yang akan dibuat"
            }
        ],
        size: "small",
        primary_action_label: __("Buat HEADER V21"),
        primary_action(values) {
            d.hide();

            frappe.call({
                method: source_type === "so"
                    ? "singlecore_apps.api.so_si_integration.make_header_v21_from_so"
                    : "singlecore_apps.api.so_si_integration.make_header_v21_from_si",
                args: {
                    [source_type === "so" ? "so_name" : "si_name"]: frm.doc.name,
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
                                    <strong>Total:</strong> ${format_currency(r.message.total_value, frm.doc.currency)}
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
// DIALOG: Pick SO to import (used from HEADER V21 form)
// ═══════════════════════════════════════════════════════════════════
function show_so_picker_dialog(frm) {
    // Fetch available SOs first
    frappe.call({
        method: "singlecore_apps.api.so_si_integration.get_available_sales_orders",
        callback: function (r) {
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__("Tidak ada Sales Order yang sudah di-submit"));
                return;
            }

            let so_options = r.message.map(so => ({
                label: `${so.name} - ${so.customer_name} (${format_currency(so.grand_total, so.currency)})`,
                value: so.name
            }));

            let d = new frappe.ui.Dialog({
                title: __("Import dari Sales Order"),
                fields: [
                    {
                        fieldname: "so_name",
                        fieldtype: "Autocomplete",
                        label: __("Pilih Sales Order"),
                        options: so_options.map(o => o.value),
                        reqd: 1
                    }
                ],
                primary_action_label: __("Import"),
                primary_action(values) {
                    d.hide();

                    frappe.call({
                        method: "singlecore_apps.api.so_si_integration.populate_header_from_so",
                        args: {
                            header_name: frm.doc.name,
                            so_name: values.so_name
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
// DIALOG: Pick SI to import (used from HEADER V21 form)
// ═══════════════════════════════════════════════════════════════════
function show_si_picker_dialog(frm) {
    frappe.call({
        method: "singlecore_apps.api.so_si_integration.get_available_sales_invoices",
        callback: function (r) {
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__("Tidak ada Sales Invoice yang sudah di-submit"));
                return;
            }

            let si_options = r.message.map(si => ({
                label: `${si.name} - ${si.customer_name} (${format_currency(si.grand_total, si.currency)})`,
                value: si.name
            }));

            let d = new frappe.ui.Dialog({
                title: __("Import dari Sales Invoice"),
                fields: [
                    {
                        fieldname: "si_name",
                        fieldtype: "Autocomplete",
                        label: __("Pilih Sales Invoice"),
                        options: si_options.map(o => o.value),
                        reqd: 1
                    }
                ],
                primary_action_label: __("Import"),
                primary_action(values) {
                    d.hide();

                    frappe.call({
                        method: "singlecore_apps.api.so_si_integration.populate_header_from_si",
                        args: {
                            header_name: frm.doc.name,
                            si_name: values.si_name
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
// DIALOG: Multi-source import for export (used from HEADER V21 form)
// ═══════════════════════════════════════════════════════════════════
function show_multi_source_export_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __("Import dari Multiple SO/SI"),
        fields: [
            {
                fieldname: "source_type",
                fieldtype: "Select",
                label: __("Jenis Sumber"),
                options: "Sales Order\nSales Invoice",
                default: "Sales Order",
                reqd: 1
            },
            {
                fieldname: "sources",
                fieldtype: "Small Text",
                label: __("Nomor Dokumen"),
                description: "Masukkan nomor dokumen, pisahkan dengan koma. Contoh: SO-001, SO-002",
                reqd: 1
            }
        ],
        primary_action_label: __("Import All"),
        primary_action(values) {
            let sources = values.sources.split(",").map(s => s.trim()).filter(s => s);
            let source_type = values.source_type === "Sales Order" ? "so" : "si";

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
                    method: source_type === "so"
                        ? "singlecore_apps.api.so_si_integration.populate_header_from_so"
                        : "singlecore_apps.api.so_si_integration.populate_header_from_si",
                    args: {
                        header_name: frm.doc.name,
                        [source_type === "so" ? "so_name" : "si_name"]: current_source
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
