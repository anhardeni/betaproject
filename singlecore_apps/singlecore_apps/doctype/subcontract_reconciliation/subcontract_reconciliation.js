// ============================================================
// Subcontract Reconciliation — Client Script
// ============================================================

frappe.ui.form.on("Subcontract Reconciliation", {

    // Saat form dimuat/refresh
    refresh(frm) {
        _set_skenario_color(frm);
        _add_custom_buttons(frm);
        _setup_filters(frm);
    },

    // Saat skenario berubah — update skenario_kode hidden field
    skenario(frm) {
        frm.set_value("skenario_kode", frm.doc.skenario && frm.doc.skenario.includes("261") ? "261" : "27");
        _set_skenario_color(frm);
        _setup_filters(frm);
    },

    // Saat header_keluar dipilih — auto-pull item barang & kontrak
    header_keluar(frm) {
        if (!frm.doc.header_keluar) return;

        frappe.call({
            method: "singlecore_apps.singlecore_apps.doctype.subcontract_reconciliation.subcontract_reconciliation.get_items_from_header",
            args: { header_name: frm.doc.header_keluar },
            freeze: true,
            freeze_message: "⏳ Menarik daftar barang & kontrak...",
            callback(r) {
                if (r.message && r.message.items) {
                    // 1. Bersihkan & Isi Tabel Barang
                    frm.clear_table("items");
                    r.message.items.forEach(row => {
                        let new_row = frm.add_child("items");
                        new_row.item_code       = row.item_code;
                        new_row.item_name       = row.item_name;
                        new_row.satuan          = row.satuan;
                        new_row.qty_keluar      = row.qty_keluar;
                        new_row.qty_masuk       = 0;
                        new_row.qty_scrap       = 0;
                        new_row.qty_outstanding = row.qty_outstanding;
                    });

                    // 2. Isi Nomor Kontrak otomatis jika ada
                    if (r.message.nomor_kontrak) {
                        frm.set_value("nomor_kontrak", r.message.nomor_kontrak);
                    }

                    frm.refresh_field("items");
                    frappe.show_alert({
                        message: `✅ ${r.message.items.length} barang ditarik. Kontrak: ${r.message.nomor_kontrak || "-"}`,
                        indicator: "green"
                    }, 5);
                } else {
                    frappe.msgprint({
                        title: "Info",
                        message: "Data ditarik namun format tidak sesuai atau kosong.",
                        indicator: "orange"
                    });
                }
            }
        });
    }
});

// ─── Filter Pencarian HEADER V21 (Smart Filtering) ──────────────────────────
function _setup_filters(frm) {
    // Filter untuk HEADER Keluar
    frm.set_query("header_keluar", () => {
        let filters = { docstatus: 1 };
        if (frm.doc.skenario_kode === "261") {
            filters.kode_dokumen = "261";
        } else {
            filters.kode_dokumen = "27";
            filters.kode_tujuan_pengeluaran = "4"; // DISUBKONTRAKAN
        }
        return { filters: filters };
    });

    // Filter untuk HEADER Masuk/Kembali
    frm.set_query("header_masuk", () => {
        let filters = { docstatus: 1 };
        if (frm.doc.skenario_kode === "261") {
            filters.kode_dokumen = "262";
            filters.kode_tujuan_pemasukan = "2"; // EKS-DISUBKONTRAKKAN
        } else {
            filters.kode_dokumen = "27";
            filters.kode_tujuan_pengeluaran = "8"; // PENGEMBALIAN SUBKONTRAK
        }
        return { filters: filters };
    });
}

// ─── Handler per-baris: Hitung ulang outstanding saat qty berubah ─────────
frappe.ui.form.on("Subcontract Reconciliation Item", {
    qty_masuk(frm, cdt, cdn) { _recalculate_row(frm, cdt, cdn); },
    qty_scrap(frm, cdt, cdn) { _recalculate_row(frm, cdt, cdn); },
    qty_keluar(frm, cdt, cdn){ _recalculate_row(frm, cdt, cdn); },
});

function _recalculate_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let outstanding = Math.max(
        (flt(row.qty_keluar) - flt(row.qty_masuk) - flt(row.qty_scrap)),
        0
    );
    frappe.model.set_value(cdt, cdn, "qty_outstanding", outstanding);

    // Update total ringkasan
    _update_totals(frm);
}

function _update_totals(frm) {
    let total_k = 0, total_m = 0, total_s = 0, total_o = 0;
    (frm.doc.items || []).forEach(r => {
        total_k += flt(r.qty_keluar);
        total_m += flt(r.qty_masuk);
        total_s += flt(r.qty_scrap);
        total_o += flt(r.qty_outstanding);
    });
    frm.set_value("total_qty_keluar",     total_k);
    frm.set_value("total_qty_masuk",      total_m);
    frm.set_value("total_qty_scrap",      total_s);
    frm.set_value("total_qty_outstanding",total_o);

    let pct = total_k > 0 ? Math.round(((total_k - total_o) / total_k) * 100) : 0;
    frm.set_value("persentase_selesai", pct);
}

// ─── Warna Indicator sesuai Status ────────────────────────────────────────
function _set_skenario_color(frm) {
    const status = frm.doc.status_rekon;
    const color_map = {
        "Outstanding": "orange",
        "Partially Settled": "yellow",
        "Settled": "green"
    };
    if (status && color_map[status]) {
        frm.page.set_indicator(status, color_map[status]);
    }
}

// ─── Custom Buttons ────────────────────────────────────────────────────────
function _add_custom_buttons(frm) {
    if (frm.doc.docstatus === 0) {
        // Tombol tarik ulang item dari header
        if (frm.doc.header_keluar) {
            frm.add_custom_button(__("🔄 Tarik Ulang Barang & Kontrak"), function() {
                frm.trigger("header_keluar");
            }, __("Tools"));
        }

        // TOMBOL BARU: Daftarkan Aju Subkon dari Luar
        frm.add_custom_button(__("📥 Daftarkan Aju Subkon (Eksternal)"), function() {
            _show_external_aju_dialog(frm);
        }, __("Tools"));
    }

    if (frm.doc.docstatus === 1 && frm.doc.status_rekon === "Settled") {
        frm.add_custom_button(__("📋 Lihat HEADER V21 Keluar"), function() {
            frappe.set_route("Form", "HEADER V21", frm.doc.header_keluar);
        });
    }
}

// ─── Dialog Registrasi Aju Eksternal (Subkon) ───────────────────────────────
function _show_external_aju_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __("Daftarkan Nomor Aju Subkon"),
        fields: [
            {
                label: __("Nomor Aju (26 Digit)"),
                fieldname: "no_aju",
                fieldtype: "Data",
                reqd: 1,
                description: "Nomor Aju yang diajukan oleh Subkon Anda"
            },
            {
                label: __("Kode Kantor"),
                fieldname: "kode_kantor",
                fieldtype: "Link",
                options: "Referensi Kantor",
                reqd: 1,
                default: "040300" // Sesuaikan dengan kantor utama Anda
            },
            {
                label: __("Jenis Dokumen"),
                fieldname: "doc_type",
                fieldtype: "Select",
                options: ["BC 2.7", "BC 2.6.2"],
                default: frm.doc.skenario_kode === "261" ? "BC 2.6.2" : "BC 2.7",
                reqd: 1
            }
        ],
        primary_action_label: __("Daftarkan & Sync"),
        primary_action(values) {
            frappe.call({
                method: "singlecore_apps.singlecore_apps.doctype.subcontract_reconciliation.subcontract_reconciliation.register_external_subcon_aju",
                args: {
                    no_aju: values.no_aju,
                    kode_kantor: values.kode_kantor,
                    doc_type: values.doc_type,
                    recon_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        d.hide();
                        frappe.msgprint({
                            title: __("Berhasil Didaftarkan"),
                            message: `Nomor Aju ${values.no_aju} telah dijadwalkan untuk ditarik. Silakan tunggu beberapa saat atau cek Status Log.`,
                            indicator: "green"
                        });
                    }
                }
            });
        }
    });
    d.show();
}
