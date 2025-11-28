/**
 * BARANG Manager - Custom Dialog for Managing BARANG with Grandchildren
 * Solves the grandchildren doctype limitation in Frappe
 * 
 * Usage: Add button in header_v2.js to call show_barang_manager(frm)
 */

function show_barang_manager(frm) {
    // Fetch all BARANG for this HEADER
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'BARANG V1',
            filters: { nomoraju: frm.doc.name },
            fields: ['name', 'seri_barang', 'uraian', 'hs', 'cif', 'netto'],
            order_by: 'seri_barang asc'
        },
        callback: function (r) {
            let barang_list = r.message || [];
            open_barang_dialog(frm, barang_list);
        }
    });
}

function open_barang_dialog(frm, barang_list) {
    let d = new frappe.ui.Dialog({
        title: __('Manage Barang & Details'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'barang_html',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function () {
            d.hide();
            frm.reload_doc();
        }
    });

    // Build HTML
    let html = build_barang_manager_html(frm, barang_list);
    d.fields_dict.barang_html.$wrapper.html(html);

    // Attach event handlers
    attach_barang_events(frm, d);

    d.show();
}

function build_barang_manager_html(frm, barang_list) {
    let html = `
        <div class="barang-manager">
            <style>
                .barang-manager { padding: 10px; }
                .barang-item { 
                    border: 1px solid #d1d8dd; 
                    margin-bottom: 15px; 
                    border-radius: 5px;
                    background: #f8f9fa;
                }
                .barang-header { 
                    background: #e8ecef; 
                    padding: 10px; 
                    cursor: pointer;
                    border-radius: 5px 5px 0 0;
                }
                .barang-header:hover { background: #dde1e4; }
                .barang-body { 
                    padding: 15px; 
                    display: none;
                }
                .barang-body.active { display: block; }
                .child-table { 
                    margin-top: 10px; 
                    width: 100%;
                }
                .child-table th { 
                    background: #5e64ff; 
                    color: white; 
                    padding: 8px;
                }
                .child-table td { 
                    padding: 8px; 
                    border: 1px solid #ddd;
                }
                .btn-add { 
                    margin-top: 10px; 
                    background: #5e64ff;
                    color: white;
                }
            </style>
            
            <div class="row">
                <div class="col-md-12">
                    <button class="btn btn-primary btn-sm" onclick="add_new_barang('${frm.doc.name}')">
                        <i class="fa fa-plus"></i> Add New Barang
                    </button>
                </div>
            </div>
            
            <div class="barang-list" style="margin-top: 15px;">
    `;

    if (barang_list.length === 0) {
        html += `
            <div class="alert alert-info">
                <i class="fa fa-info-circle"></i> 
                No barang found. Click "Add New Barang" to start.
            </div>
        `;
    } else {
        barang_list.forEach(function (barang, index) {
            html += build_barang_item_html(barang, index);
        });
    }

    html += `
            </div>
        </div>
    `;

    return html;
}

function build_barang_item_html(barang, index) {
    return `
        <div class="barang-item" data-barang="${barang.name}">
            <div class="barang-header" onclick="toggle_barang('${barang.name}')">
                <strong>Barang ${barang.seri_barang}: ${barang.uraian || 'No Description'}</strong>
                <span class="pull-right">
                    <small>HS: ${barang.hs || '-'} | CIF: ${barang.cif || 0} | Netto: ${barang.netto || 0}</small>
                    <i class="fa fa-chevron-down toggle-icon"></i>
                </span>
            </div>
            
            <div class="barang-body" id="body-${barang.name}">
                <div class="row">
                    <div class="col-md-12">
                        <button class="btn btn-sm btn-default" onclick="edit_barang('${barang.name}')">
                            <i class="fa fa-edit"></i> Edit Barang
                        </button>
                        <button class="btn btn-sm btn-danger pull-right" onclick="delete_barang('${barang.name}')">
                            <i class="fa fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
                
                <!-- BARANG TARIF Section -->
                <div class="tarif-section" style="margin-top: 15px;">
                    <h5><i class="fa fa-calculator"></i> Tarif & Pungutan</h5>
                    <table class="table table-bordered child-table">
                        <thead>
                            <tr>
                                <th width="20%">Kode Pungutan</th>
                                <th width="15%">Kode Tarif</th>
                                <th width="15%">Tarif (%)</th>
                                <th width="20%">Nilai Bayar</th>
                                <th width="20%">Nilai Fasilitas</th>
                                <th width="10%">Action</th>
                            </tr>
                        </thead>
                        <tbody id="tarif-${barang.name}">
                            <tr>
                                <td colspan="6" class="text-center">
                                    <i class="fa fa-spinner fa-spin"></i> Loading...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <button class="btn btn-sm btn-add" onclick="add_tarif('${barang.name}')">
                        <i class="fa fa-plus"></i> Add Tarif
                    </button>
                </div>
                
                <!-- BARANG DOKUMEN Section -->
                <div class="dokumen-section" style="margin-top: 20px;">
                    <h5><i class="fa fa-file-text"></i> Dokumen</h5>
                    <table class="table table-bordered child-table">
                        <thead>
                            <tr>
                                <th width="40%">Seri Dokumen</th>
                                <th width="40%">Seri Izin</th>
                                <th width="20%">Action</th>
                            </tr>
                        </thead>
                        <tbody id="dokumen-${barang.name}">
                            <tr>
                                <td colspan="3" class="text-center">
                                    <i class="fa fa-spinner fa-spin"></i> Loading...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <button class="btn btn-sm btn-add" onclick="add_dokumen('${barang.name}')">
                        <i class="fa fa-plus"></i> Add Dokumen
                    </button>
                </div>
                
                <!-- BARANG SPEK KHUSUS Section -->
                <div class="spek-section" style="margin-top: 20px;">
                    <h5><i class="fa fa-cog"></i> Spesifikasi Khusus</h5>
                    <div id="spek-${barang.name}">
                        <i class="fa fa-spinner fa-spin"></i> Loading...
                    </div>
                    <button class="btn btn-sm btn-add" onclick="add_spek_khusus('${barang.name}')">
                        <i class="fa fa-plus"></i> Add Spek Khusus
                    </button>
                </div>
            </div>
        </div>
    `;
}

function attach_barang_events(frm, dialog) {
    // Load child data for each barang when expanded
    setTimeout(function () {
        $('.barang-item').each(function () {
            let barang_name = $(this).data('barang');
            load_barang_children(barang_name);
        });
    }, 500);
}

function toggle_barang(barang_name) {
    let body = $('#body-' + barang_name);
    body.toggleClass('active');

    // Toggle icon
    let icon = body.prev().find('.toggle-icon');
    if (body.hasClass('active')) {
        icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
    } else {
        icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
    }
}

function load_barang_children(barang_name) {
    // Load BARANG TARIF
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'BARANG TARIF',
            filters: { parent: barang_name },
            fields: ['name', 'kode_pungutan', 'kode_tarif', 'tarif', 'nilai_bayar', 'nilai_fasilitas'],
            order_by: 'idx asc'
        },
        callback: function (r) {
            render_tarif_list(barang_name, r.message || []);
        }
    });

    // Load BARANG DOKUMEN
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'BARANG DOKUMEN',
            filters: { parent: barang_name },
            fields: ['name', 'seri_dokumen', 'seri_izin'],
            order_by: 'idx asc'
        },
        callback: function (r) {
            render_dokumen_list(barang_name, r.message || []);
        }
    });
}

function render_tarif_list(barang_name, tarif_list) {
    let html = '';

    if (tarif_list.length === 0) {
        html = '<tr><td colspan="6" class="text-center text-muted">No tarif added yet</td></tr>';
    } else {
        tarif_list.forEach(function (tarif) {
            html += `
                <tr>
                    <td>${tarif.kode_pungutan || '-'}</td>
                    <td>${tarif.kode_tarif || '-'}</td>
                    <td>${tarif.tarif || 0}</td>
                    <td>${format_currency(tarif.nilai_bayar || 0)}</td>
                    <td>${format_currency(tarif.nilai_fasilitas || 0)}</td>
                    <td>
                        <button class="btn btn-xs btn-default" onclick="edit_tarif('${tarif.name}')">
                            <i class="fa fa-edit"></i>
                        </button>
                        <button class="btn btn-xs btn-danger" onclick="delete_tarif('${tarif.name}', '${barang_name}')">
                            <i class="fa fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    $('#tarif-' + barang_name).html(html);
}

function render_dokumen_list(barang_name, dokumen_list) {
    let html = '';

    if (dokumen_list.length === 0) {
        html = '<tr><td colspan="3" class="text-center text-muted">No dokumen added yet</td></tr>';
    } else {
        dokumen_list.forEach(function (dok) {
            html += `
                <tr>
                    <td>${dok.seri_dokumen || '-'}</td>
                    <td>${dok.seri_izin || '-'}</td>
                    <td>
                        <button class="btn btn-xs btn-default" onclick="edit_dokumen('${dok.name}')">
                            <i class="fa fa-edit"></i>
                        </button>
                        <button class="btn btn-xs btn-danger" onclick="delete_dokumen('${dok.name}', '${barang_name}')">
                            <i class="fa fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    $('#dokumen-' + barang_name).html(html);
}

// Helper functions
function format_currency(value) {
    return parseFloat(value || 0).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// CRUD Functions
function add_new_barang(nomoraju) {
    frappe.new_doc('BARANG V1', {
        nomoraju: nomoraju
    });
}

function edit_barang(barang_name) {
    frappe.set_route('Form', 'BARANG V1', barang_name);
}

function delete_barang(barang_name) {
    frappe.confirm(
        __('Are you sure you want to delete this barang?'),
        function () {
            frappe.call({
                method: 'frappe.client.delete',
                args: {
                    doctype: 'BARANG V1',
                    name: barang_name
                },
                callback: function () {
                    frappe.show_alert({ message: __('Barang deleted'), indicator: 'green' });
                    $('[data-barang="' + barang_name + '"]').remove();
                }
            });
        }
    );
}

function add_tarif(barang_name) {
    let d = new frappe.ui.Dialog({
        title: __('Add Tarif'),
        fields: [
            {
                fieldname: 'kode_pungutan',
                fieldtype: 'Link',
                label: __('Kode Pungutan'),
                options: 'Referensi Jenis Pungutan',
                reqd: 1
            },
            {
                fieldname: 'kode_tarif',
                fieldtype: 'Link',
                label: __('Kode Tarif'),
                options: 'Referensi Jenis Tarif',
                reqd: 1
            },
            {
                fieldname: 'tarif',
                fieldtype: 'Float',
                label: __('Tarif (%)'),
                precision: 2
            },
            {
                fieldname: 'nilai_bayar',
                fieldtype: 'Currency',
                label: __('Nilai Bayar')
            },
            {
                fieldname: 'nilai_fasilitas',
                fieldtype: 'Currency',
                label: __('Nilai Fasilitas')
            }
        ],
        primary_action_label: __('Add'),
        primary_action: function (values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'BARANG TARIF',
                        parent: barang_name,
                        parenttype: 'BARANG V1',
                        parentfield: 'barang_tarif',
                        ...values
                    }
                },
                callback: function () {
                    frappe.show_alert({ message: __('Tarif added'), indicator: 'green' });
                    load_barang_children(barang_name);
                    d.hide();
                }
            });
        }
    });
    d.show();
}

function edit_tarif(tarif_name) {
    frappe.set_route('Form', 'BARANG TARIF', tarif_name);
}

function delete_tarif(tarif_name, barang_name) {
    frappe.confirm(
        __('Delete this tarif?'),
        function () {
            frappe.call({
                method: 'frappe.client.delete',
                args: {
                    doctype: 'BARANG TARIF',
                    name: tarif_name
                },
                callback: function () {
                    frappe.show_alert({ message: __('Tarif deleted'), indicator: 'green' });
                    load_barang_children(barang_name);
                }
            });
        }
    );
}

function add_dokumen(barang_name) {
    let d = new frappe.ui.Dialog({
        title: __('Add Dokumen'),
        fields: [
            {
                fieldname: 'seri_dokumen',
                fieldtype: 'Int',
                label: __('Seri Dokumen'),
                reqd: 1
            },
            {
                fieldname: 'seri_izin',
                fieldtype: 'Int',
                label: __('Seri Izin')
            }
        ],
        primary_action_label: __('Add'),
        primary_action: function (values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'BARANG DOKUMEN',
                        parent: barang_name,
                        parenttype: 'BARANG V1',
                        parentfield: 'barang_dokumen',
                        ...values
                    }
                },
                callback: function () {
                    frappe.show_alert({ message: __('Dokumen added'), indicator: 'green' });
                    load_barang_children(barang_name);
                    d.hide();
                }
            });
        }
    });
    d.show();
}

function edit_dokumen(dokumen_name) {
    frappe.set_route('Form', 'BARANG DOKUMEN', dokumen_name);
}

function delete_dokumen(dokumen_name, barang_name) {
    frappe.confirm(
        __('Delete this dokumen?'),
        function () {
            frappe.call({
                method: 'frappe.client.delete',
                args: {
                    doctype: 'BARANG DOKUMEN',
                    name: dokumen_name
                },
                callback: function () {
                    frappe.show_alert({ message: __('Dokumen deleted'), indicator: 'green' });
                    load_barang_children(barang_name);
                }
            });
        }
    );
}

function add_spek_khusus(barang_name) {
    frappe.msgprint(__('Spek Khusus feature coming soon...'));
}
