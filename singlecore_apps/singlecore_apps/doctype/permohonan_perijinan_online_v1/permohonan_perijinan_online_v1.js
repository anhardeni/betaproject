// Copyright (c) 2023, AnharDeni and contributors
// For license information, please see license.txt

frappe.ui.form.on('PERMOHONAN PERIJINAN ONLINE V1', {
	// refresh: function(frm) {

	// }

	refresh: function(frm) {
        frm.add_custom_button('Create Membership', () => {
            frappe.new_doc('PERMOHONAN PERIJINAN ONLINE V1', {
                permohonan_perijinan_online_v1: frm.doc.name
            })
        })
        frm.add_custom_button('Create Transaction', () => {
            frappe.new_doc('PERMOHONAN PERIJINAN ONLINE V1', {
                permohonan_perijinan_online_v1: frm.doc.name
            })
        })

		frm.set_value({
			jaminan_in_words: 'tujuh ratus'
		})
		
    }
});
