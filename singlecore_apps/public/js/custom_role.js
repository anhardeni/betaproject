frappe.ui.form.on('Role', {
    refresh: function (frm) {
        if (frappe.user.has_role('System Manager') && !frm.is_new()) {
            frm.add_custom_button('🔧 Beri Akses Singlecore', () => {
                frappe.call({
                    // Path fungsinya HARUS lokasi absoulut python Anda
                    method: 'singlecore_apps.api.permissions.set_singlecore_role',
                    args: { target_role: frm.doc.role_name },
                    callback: function (r) {
                        if (r.message && r.message.status == "success") {
                            frappe.msgprint(r.message.message);
                        }
                    }
                });
            });
        }
    }
});
