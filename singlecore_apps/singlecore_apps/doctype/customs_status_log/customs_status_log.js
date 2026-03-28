// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customs Status Log", {
    refresh(frm) {
        // Jika Dokumen adalah Tipe Eksternal dan Belum Selesai Ditarik
        if (frm.doc.is_external_doc && frm.doc.bc_status !== "Completed") {

            // Tampilkan tombol "Sync Detail (Eksternal)" di menu Action
            frm.add_custom_button(__('Sync Detail (Eksternal)'), function () {
                frappe.call({
                    method: "singlecore_apps.api.ceisa_api.external_sync.trigger_sync_now",
                    args: { log_name: frm.doc.name },
                    freeze: true,
                    freeze_message: "Sedang menarik data dari API CEISA...",
                    callback: function (r) {
                        if (r.message && r.message[0]) {
                            // Jika True (Berhasil) -> Notifikasi Hijau
                            frappe.msgprint({ title: __('Sukses'), message: r.message[1], indicator: 'green' });
                            frm.reload_doc(); // Supaya status langsung berubah jadi Completed di form
                        } else {
                            // Jika False (PPJK Belum Submit) -> Notifikasi Oranye
                            frappe.msgprint({ title: __('Proses Polling'), message: r.message[1], indicator: 'orange' });
                            frm.reload_doc(); // Supaya Next Polling Time yang baru ter-update di form
                        }
                    }
                });
            }, __("Actions"));
        }


    },
});
