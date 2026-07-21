frappe.listview_settings['BAHAN BAKU'] = {
	onload: function(listview) {
		const url_params = new URLSearchParams(window.location.search);
		
		// 1. Ambil & Simpan Parent Barang
		const parent_barang = url_params.get('parent_barang') || (frappe.route_options && frappe.route_options.parent_barang);
		if (parent_barang) {
			sessionStorage.setItem('last_parent_barang', parent_barang);
			listview.page.add_inner_button(__('Back to BARANG V1'), function() {
				frappe.set_route('Form', 'BARANG V1', parent_barang);
			});
		}

		// 2. Ambil & Simpan Nomor Aju
		const nomoraju = url_params.get('nomoraju') || (frappe.route_options && frappe.route_options.nomoraju);
		if (nomoraju) {
			sessionStorage.setItem('last_nomoraju', nomoraju);
			listview.page.add_inner_button(__('Back to HEADER V21'), function() {
				frappe.set_route('Form', 'HEADER V21', nomoraju);
			});
		}
	},

	refresh: function(listview) {
		const url_params = new URLSearchParams(window.location.search);
		
		// Update sessionStorage jika ada parameter parent_barang atau nomoraju aktif di parameter URL/route (untuk caching SPA navigation)
		const parent_barang_aktif = url_params.get('parent_barang') || (frappe.route_options && frappe.route_options.parent_barang);
		if (parent_barang_aktif) {
			sessionStorage.setItem('last_parent_barang', parent_barang_aktif);
		}
		
		const nomoraju_aktif = url_params.get('nomoraju') || (frappe.route_options && frappe.route_options.nomoraju);
		if (nomoraju_aktif) {
			sessionStorage.setItem('last_nomoraju', nomoraju_aktif);
		}

		const filters = listview.filter_area.get();
		
		// Cek apakah ada salah satu filter wajib yang terpasang di UI
		const has_parent_barang = filters.some(f => f[1] === 'parent_barang');
		const has_nomoraju = filters.some(f => f[1] === 'nomoraju');

		// Jika TIDAK ADA filter wajib sama sekali di UI (misal karena dihapus silang [x] oleh user)
		if (!has_parent_barang && !has_nomoraju) {
			const last_parent = sessionStorage.getItem('last_parent_barang');
			const last_nomoraju = sessionStorage.getItem('last_nomoraju');

			if (last_parent) {
				// Pulihkan ke filter barang terakhir
				listview.filter_area.add(listview.doctype, 'parent_barang', '=', last_parent);
				frappe.show_alert({ message: __('Filter dipulihkan ke Barang aktif.'), indicator: 'orange' });
			} else if (last_nomoraju) {
				// Pulihkan ke filter nomor aju terakhir
				listview.filter_area.add(listview.doctype, 'nomoraju', '=', last_nomoraju);
				frappe.show_alert({ message: __('Filter dipulihkan ke Nomor Aju aktif.'), indicator: 'orange' });
			} else {
				// Jika benar-benar tidak ada konteks dokumen, redirect paksa demi keamanan database
				frappe.msgprint({
					title: __('Akses Dibatasi'),
					message: __('Anda harus masuk melalui dokumen HEADER V21 atau BARANG V1 terlebih dahulu untuk melihat Bahan Baku.'),
					indicator: 'red'
				});
				frappe.set_route('List', 'HEADER V21');
			}
		}
	}
};
