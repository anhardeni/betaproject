// ============================================================
// Subcontract Reconciliation — Client Script
// ============================================================

frappe.ui.form.on("Subcontract Reconciliation", {

    // Saat form dimuat/refresh
    refresh(frm) {
        _set_skenario_color(frm);
        _add_custom_buttons(frm);
    },

    // Saat skenario berubah — update skenario_kode hidden field
    skenario(frm) {
        frm.set_value("skenario_kode", frm.doc.skenario && frm.doc.skenario.includes("261") ? "261" : "27");
        _set_skenario_color(frm);
    },

    // Saat header_keluar dipilih — auto-pull item barang
    header_keluar(frm) {
        if (!frm.doc.header_keluar) return;

        frappe.call({
            method: "singlecore_apps.singlecore_apps.doctype.subcontract_reconciliation.subcontract_reconciliation.get_items_from_header",
            args: { header_name: frm.doc.header_keluar },
            freeze: true,
            freeze_message: "⏳ Menarik daftar barang dari HEADER V21...",
            callback(r) {
                if (r.message && r.message.length > 0) {
                    // Bersihkan tabel dulu
                    frm.clear_table("items");

                    // Isi dari hasil API
                    r.message.forEach(row => {
                        let new_row = frm.add_child("items");
                        new_row.item_code       = row.item_code;
                        new_row.item_name       = row.item_name;
                        new_row.satuan          = row.satuan;
                        new_row.qty_keluar      = row.qty_keluar;
                        new_row.qty_masuk       = 0;
                        new_row.qty_scrap       = 0;
                        new_row.qty_outstanding = row.qty_outstanding;
                    });

                    frm.refresh_field("items");
                    frappe.show_alert({
                        message: `✅ ${r.message.length} barang berhasil ditarik dari HEADER V21.`,
                        indicator: "green"
                    }, 5);
                } else {
                    frappe.msgprint({
                        title: "Info",
                        message: "Tidak ada barang yang ditemukan di HEADER V21 tersebut, atau child table BARANG kosong.",
                        indicator: "orange"
                    });
                }
            }
        });
    }
});

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
            frm.add_custom_button(__("🔄 Tarik Ulang Barang dari Header"), function() {
                frm.trigger("header_keluar");
            }, __("Tools"));
        }
    }

    if (frm.doc.docstatus === 1 && frm.doc.status_rekon === "Settled") {
        frm.add_custom_button(__("📋 Lihat HEADER V21 Keluar"), function() {
            frappe.set_route("Form", "HEADER V21", frm.doc.header_keluar);
        });
    }
}
