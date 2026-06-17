frappe.listview_settings['BARANG V1'] = {
	onload: function(listview) {
		const url_params = new URLSearchParams(window.location.search);
		const nomoraju = url_params.get('nomoraju') || (frappe.route_options && frappe.route_options.nomoraju);
		if (nomoraju) {
			listview.page.add_inner_button(__('Back to HEADER V21'), function() {
				frappe.set_route('Form', 'HEADER V21', nomoraju);
			});
		}
	}
};
