
js_code = """
function add_beacukai_actions(frm) {
    frm.add_custom_button(__('🔐 Login Beacukai'), function() {
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
            primary_action: function(values) {
                frappe.call({
                    method: 'singlecore_apps.api.login_beacukai',
                    args: {
                        username: values.username,
                        password: values.password
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.msgprint('Login Successful');
                            d.hide();
                        } else {
                            frappe.msgprint('Login Failed: ' + (r.message ? r.message.message : 'Unknown error'));
                        }
                    }
                });
            }
        });
        d.show();
    }, __('Beacukai'));

    frm.add_custom_button(__('📤 Send Document'), function() {
        frappe.confirm('Are you sure you want to send this document to Beacukai?', function() {
            frappe.call({
                method: 'singlecore_apps.api.send_ceisa_document',
                args: {
                    docname: frm.doc.nomoraju || frm.doc.name
                },
                freeze: true,
                freeze_message: 'Sending to Beacukai...',
                callback: function(r) {
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
    }, __('Beacukai'));

    frm.add_custom_button(__('🔄 Check Status'), function() {
        frappe.call({
            method: 'singlecore_apps.api.check_ceisa_status',
            args: {
                nomor_aju: frm.doc.nomoraju || frm.doc.name
            },
            freeze: true,
            callback: function(r) {
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
    }, __('Beacukai'));
}
"""

with open("/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/singlecore_apps/doctype/header_v21/header_v21.js", "a") as f:
    f.write(js_code)
