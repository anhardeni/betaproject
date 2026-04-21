/**
 * Customs Status Log — Client Script
 * ====================================
 * Adds:
 *  1. "Pull Status Now" button on the form toolbar
 *  2. Colour-coded bc_status badge indicator in the form dashboard
 *  3. "Open PDF" links in the Response History child table grid
 */

frappe.ui.form.on("Customs Status Log", {

    // ── Lifecycle ──────────────────────────────────────────────────────────
    refresh(frm) {
        _render_status_badge(frm);
        _add_pull_button(frm);
        _make_children_readonly(frm);
    },

    bc_status(frm) {
        _render_status_badge(frm);
    },
});


// ════════════════════════════════════════════════════════════════════════════
// Status badge
// ════════════════════════════════════════════════════════════════════════════

const STATUS_COLORS = {
    "Pending": "orange",
    "Registered": "blue",
    "Completed": "green",
    "Rejected": "red",
    "On Hold": "gray",
};

function _render_status_badge(frm) {
    // Remove old badge if any
    frm.dashboard.clear_headline();

    const status = frm.doc.bc_status;
    if (!status) return;

    const color = STATUS_COLORS[status] || "gray";
    frm.page.set_indicator(status, color);

    // If NOPEN is set, show it next to the badge
    if (frm.doc.nopen) {
        frm.dashboard.set_headline(
            `<span class="indicator-pill ${color} filterable">${status}</span>
             &nbsp;NOPEN: <strong>${frm.doc.nopen}</strong>
             ${frm.doc.nopen_date ? " — " + frappe.datetime.str_to_user(frm.doc.nopen_date) : ""}`
        );
    }
}


// ════════════════════════════════════════════════════════════════════════════
// Pull Status Now button
// ════════════════════════════════════════════════════════════════════════════

function _add_pull_button(frm) {
    // Only show when the record is saved and has a no_aju
    if (frm.doc.__islocal || !frm.doc.no_aju) return;

    frm.add_custom_button(__("Pull Status Now"), function () {
        frappe.confirm(
            __("Tarik status terbaru dari CEISA untuk <strong>{0}</strong>?", [frm.doc.no_aju]),
            function () {
                _do_pull(frm);
            }
        );
    }, __("Bea Cukai"));

    // Also add a direct link to the linked BC document if set
    if (frm.doc.linked_document_type && frm.doc.linked_document_name) {
        frm.add_custom_button(
            __("Buka {0}", [frm.doc.linked_document_name]),
            function () {
                frappe.set_route("Form", frm.doc.linked_document_type, frm.doc.linked_document_name);
            },
            __("Bea Cukai")
        );
    }
    
    // Download Raw JSON button
    frm.add_custom_button(
        __("Download Raw JSON"),
        function () {
            if (!frm.doc.last_response_raw) {
                frappe.msgprint(__("Belum ada data raw. Klik 'Pull Status Now' terlebih dahulu."));
                return;
            }
            const filename = `Status_${frm.doc.no_aju}.json`;
            const data = frm.doc.last_response_raw;
            _download_json(data, filename);
        },
        __("Bea Cukai")
    );
}

function _download_json(data, filename) {
    const jsonStr = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function _do_pull(frm) {
    frm.disable_save();
    frappe.show_progress(__("Menarik status…"), 50, 100, __("Menghubungi CEISA API…"));

    frappe.call({
        method: "singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log.pull_status_now",
        args: { log_name: frm.doc.name },
        freeze: true,
        freeze_message: __("Menarik status dari Bea Cukai…"),
        callback(r) {
            frappe.hide_progress();
            frm.enable_save();

            if (!r.exc && r.message) {
                const msg = r.message;
                if (msg.status === "success") {
                    frappe.show_alert({
                        message: __(
                            "Berhasil: +{0} status baru, +{1} respon baru. Status: <strong>{2}</strong>",
                            [msg.added_statuses, msg.added_responses, msg.bc_status]
                        ),
                        indicator: "green"
                    }, 8);
                    frm.reload_doc();
                } else if (msg.status === "no_change") {
                    frappe.msgprint({
                        title: __("Tidak Ada Perubahan"),
                        indicator: "blue",
                        message: __("Data dari Bea Cukai masih sama dengan data terakhir di sistem.")
                    });
                } else {
                    frappe.msgprint({
                        title: __("Pull Status Gagal"),
                        indicator: "red",
                        message: msg.message || JSON.stringify(msg),
                    });
                }
            }
        },
        error() {
            frappe.hide_progress();
            frm.enable_save();
            frappe.msgprint({
                title: __("Error"),
                indicator: "red",
                message: __("Terjadi error saat tarik status. Lihat Error Log.")
            });
        }
    });
}


// ════════════════════════════════════════════════════════════════════════════
// Child table: make read-only for non-privileged users
// ════════════════════════════════════════════════════════════════════════════

function _make_children_readonly(frm) {
    // EXIM Staff can only view child rows, not edit them manually.
    // System Manager and EXIM Manager can edit.
    const editable_roles = ["System Manager", "EXIM Manager"];
    const can_edit = frappe.user_roles.some(r => editable_roles.includes(r));

    if (!can_edit) {
        frm.set_df_property("statuses", "cannot_add_rows", true);
        frm.set_df_property("statuses", "cannot_delete_rows", true);
        frm.set_df_property("responses", "cannot_add_rows", true);
        frm.set_df_property("responses", "cannot_delete_rows", true);
    }
}
