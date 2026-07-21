frappe.listview_settings['BARANG V1'] = {
	onload: function(listview) {
		const url_params = new URLSearchParams(window.location.search);
		const nomoraju = url_params.get('nomoraju') || (frappe.route_options && frappe.route_options.nomoraju);
		
		if (nomoraju) {
			sessionStorage.setItem('last_nomoraju', nomoraju);
			listview.page.add_inner_button(__('Back to HEADER V21'), function() {
				frappe.set_route('Form', 'HEADER V21', nomoraju);
			});
		}
	},

	refresh: function(listview) {
		// Update sessionStorage jika ada nomoraju aktif di parameter URL/route (untuk caching SPA navigation)
		const url_params = new URLSearchParams(window.location.search);
		const nomoraju_aktif = url_params.get('nomoraju') || (frappe.route_options && frappe.route_options.nomoraju);
		if (nomoraju_aktif) {
			sessionStorage.setItem('last_nomoraju', nomoraju_aktif);
		}

		const filters = listview.filter_area.get();
		const has_nomoraju = filters.some(f => f[1] === 'nomoraju');
		
		// Jika filter nomoraju dikosongkan/dihapus oleh user, pulihkan demi keamanan performa database
		if (!has_nomoraju) {
			const last_nomoraju = sessionStorage.getItem('last_nomoraju');
			if (last_nomoraju) {
				listview.filter_area.add(listview.doctype, 'nomoraju', '=', last_nomoraju);
				frappe.show_alert({ message: __('Filter dipulihkan ke Nomor Aju aktif.'), indicator: 'orange' });
			} else {
				frappe.msgprint({
					title: __('Akses Dibatasi'),
					message: __('Anda harus masuk melalui dokumen HEADER V21 terlebih dahulu untuk melihat daftar barang.'),
					indicator: 'red'
				});
				frappe.set_route('List', 'HEADER V21');
			}
		}
	}
};
