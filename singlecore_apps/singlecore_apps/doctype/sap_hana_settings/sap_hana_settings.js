frappe.ui.form.on("SAP HANA Settings", {
    refresh(frm) {
        // Tombol 1: Test Connection
        frm.add_custom_button(__("🔌 Test Connection"), function() {
            frappe.call({
                method: "singlecore_apps.singlecore_apps.doctype.sap_hana_settings.sap_hana_settings.test_connection",
                freeze: true,
                freeze_message: __("Menguji koneksi ke server SAP HANA..."),
                callback: function(r) {
                    if (r.message) {
                        let ind = r.message.status === "success" ? "green" : (r.message.status === "warning" ? "orange" : "red");
                        frappe.msgprint({
                            title: __("Hasil Pengujian Koneksi"),
                            indicator: ind,
                            message: r.message.message
                        });
                    }
                }
            });
        }).addClass("btn-primary");

        // Tombol 2: Langsung Buka Dashboard
        frm.add_custom_button(__("📊 Buka Sync Dashboard"), function() {
            frappe.set_route("sap_hana_dashboard");
        });
    }
});
