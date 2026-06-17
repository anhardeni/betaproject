frappe.listview_settings['BAHAN BAKU'] = {
	onload: function(listview) {
		const url_params = new URLSearchParams(window.location.search);
		const parent_barang = url_params.get('parent_barang') || (frappe.route_options && frappe.route_options.parent_barang);
		if (parent_barang) {
			listview.page.add_inner_button(__('Back to BARANG V1'), function() {
				frappe.set_route('Form', 'BARANG V1', parent_barang);
			});
		}
	}
};
