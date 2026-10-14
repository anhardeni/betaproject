frappe.pages['sap_hana_dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('SAP HANA Integration Dashboard'),
        single_column: true
    });

    // ── 1. Page Header Action Buttons ──────────────────────────────────────────
    page.set_primary_action(__('🚀 Sync SAP HANA Sekarang'), function() {
        run_sap_sync(page);
    }, 'octicon octicon-sync');

    page.add_button(__('🧹 Bersihkan Log'), function() {
        $('#sap-console-log').html('<div class="log-entry text-muted">[System] Log dibersihkan. Siap untuk sinkronisasi berikutnya.</div>');
    });

    // ── 2. Date Range Filters ──────────────────────────────────────────────────
    let first_day = frappe.datetime.month_start();
    let today = frappe.datetime.get_today();

    let from_date_field = page.add_field({
        fieldname: 'from_date',
        label: __('Dari Tanggal'),
        fieldtype: 'Date',
        default: first_day
    });

    let to_date_field = page.add_field({
        fieldname: 'to_date',
        label: __('Sampai Tanggal'),
        fieldtype: 'Date',
        default: today
    });

    // ── 3. Render Dashboard Body ───────────────────────────────────────────────
    let html_content = `
    <div class="sap-dashboard-container" style="padding: 10px 0 30px 0;">
        
        <!-- Banner Info Arsitektur -->
        <div class="card mb-4" style="border-radius: 8px; border-left: 5px solid #2490ef; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-1" style="font-weight: 600; color: #1f272e;">
                            <span class="indicator-pill green mr-2"></span> SingleCore Direct Bridge (SAP HANA &rarr; ERPNext 15)
                        </h5>
                        <p class="text-muted mb-0" style="font-size: 13px;">
                            Arsitektur Hub-and-Spoke langsung tanpa middleware pihak ketiga. Mendukung penarikan berkala via Background Worker & eksekusi instan on-demand.
                        </p>
                    </div>
                    <div class="text-right">
                        <span class="badge badge-success px-2 py-1" style="font-size: 12px; font-weight: 500;">
                            Status: Siap (Ready)
                        </span>
                        <div class="text-muted mt-1" style="font-size: 11px;">Jadwal: Hourly Cron (Tiap Jam)</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- KPI Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card p-3 text-center" style="border-radius: 8px; background: #fbfcfd; border: 1px solid #e2e8f0;">
                    <div class="text-muted" style="font-size: 12px; font-weight: 600; text-transform: uppercase;">SAP Pemasukan Extracted</div>
                    <div id="kpi-pemasukan-extracted" style="font-size: 28px; font-weight: 700; color: #1a202c; margin: 8px 0;">0</div>
                    <div class="text-muted" style="font-size: 11px;">Dokumen dari SAP HANA</div>
                </div>
            </div>
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card p-3 text-center" style="border-radius: 8px; background: #f0fdf4; border: 1px solid #bbf7d0;">
                    <div class="text-muted" style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #166534 !important;">Pemasukan Synced</div>
                    <div id="kpi-pemasukan-synced" style="font-size: 28px; font-weight: 700; color: #15803d; margin: 8px 0;">0</div>
                    <div class="text-muted" style="font-size: 11px;">Tersimpan di Purchase Receipt</div>
                </div>
            </div>
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card p-3 text-center" style="border-radius: 8px; background: #fbfcfd; border: 1px solid #e2e8f0;">
                    <div class="text-muted" style="font-size: 12px; font-weight: 600; text-transform: uppercase;">SAP Pengeluaran Extracted</div>
                    <div id="kpi-pengeluaran-extracted" style="font-size: 28px; font-weight: 700; color: #1a202c; margin: 8px 0;">0</div>
                    <div class="text-muted" style="font-size: 11px;">Dokumen dari SAP HANA</div>
                </div>
            </div>
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="card p-3 text-center" style="border-radius: 8px; background: #eff6ff; border: 1px solid #bfdbfe;">
                    <div class="text-muted" style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #1e40af !important;">Pengeluaran Synced</div>
                    <div id="kpi-pengeluaran-synced" style="font-size: 28px; font-weight: 700; color: #2563eb; margin: 8px 0;">0</div>
                    <div class="text-muted" style="font-size: 11px;">Tersimpan di Delivery Note</div>
                </div>
            </div>
        </div>

        <!-- Quick Access Shortcuts -->
        <div class="card mb-4" style="border-radius: 8px; border: 1px solid #e2e8f0;">
            <div class="card-body p-3">
                <span class="font-weight-bold mr-3" style="font-size: 13px; color: #4a5568;">Akses Cepat Dokumen & Laporan:</span>
                <a href="/app/sap-hana-settings" class="btn btn-xs btn-primary mr-2" style="font-size: 12px; color: #fff !important;">⚙️ Pengaturan SAP HANA</a>
                <a href="/app/purchase-receipt" class="btn btn-xs btn-default mr-2" style="font-size: 12px;">📦 Purchase Receipt List</a>
                <a href="/app/delivery-note" class="btn btn-xs btn-default mr-2" style="font-size: 12px;">🚚 Delivery Note List</a>
                <a href="/app/query-report/Laporan%20Pemasukan%20Barang%20Bea%20Cukai" class="btn btn-xs btn-default mr-2" style="font-size: 12px;">📑 Laporan Pemasukan KEK</a>
                <a href="/app/query-report/Laporan%20Pengeluaran%20Barang" class="btn btn-xs btn-default" style="font-size: 12px;">📑 Laporan Pengeluaran KEK</a>
            </div>
        </div>

        <!-- Live Sync Terminal / Activity Log -->
        <div class="card" style="border-radius: 8px; border: 1px solid #cbd5e1; overflow: hidden;">
            <div class="card-header bg-dark text-white p-3 d-flex justify-content-between align-items-center" style="background-color: #1e293b !important;">
                <span style="font-weight: 600; font-size: 13px; letter-spacing: 0.5px;">🖥️ AKTIVITAS SINKRONISASI REAL-TIME (CONSOLE LOG)</span>
                <span id="sync-last-timestamp" class="text-muted" style="font-size: 11px; color: #94a3b8 !important;">Belum ada eksekusi</span>
            </div>
            <div id="sap-console-log" style="background-color: #0f172a; color: #38bdf8; font-family: 'Courier New', Courier, monospace; font-size: 12px; padding: 16px; min-height: 220px; max-height: 400px; overflow-y: auto; line-height: 1.6;">
                <div class="log-entry text-muted">[System] Dashboard SAP HANA siap. Pilih range tanggal lalu klik tombol "Sync SAP HANA Sekarang".</div>
            </div>
        </div>

    </div>
    `;

    $(page.body).html(html_content);

    // ── 4. Fungsi Eksekusi Sinkronisasi ────────────────────────────────────────
    function run_sap_sync(page) {
        let from_date = page.fields_dict.from_date.get_value() || first_day;
        let to_date = page.fields_dict.to_date.get_value() || today;

        let now_str = frappe.datetime.now_datetime();
        $('#sync-last-timestamp').text('Terakhir run: ' + now_str);

        append_log(`[${now_str}] 🚀 Memulai penarikan data dari SAP HANA (${from_date} s/d ${to_date})...`, '#fbbf24');
        append_log(`[${now_str}] Menghubungkan ke direct pipeline SAP HANA -> ERPNext 15...`, '#94a3b8');

        frappe.call({
            method: 'singlecore_apps.utils.sync_engine_direct.trigger_direct_sync',
            args: {
                from_date: from_date,
                to_date: to_date
            },
            freeze: true,
            freeze_message: __('⏳ Menghubungi SAP HANA & Sinkronisasi Dokumen ke ERPNext...'),
            callback: function(r) {
                let finish_time = frappe.datetime.now_datetime();
                if (r.exc) {
                    append_log(`[${finish_time}] ❌ ERROR: Gagal mengeksekusi pipeline SAP HANA: ${r.exc}`, '#f87171');
                    frappe.msgprint({
                        title: __('Sinkronisasi Gagal'),
                        indicator: 'red',
                        message: __('Terjadi kesalahan saat memproses data SAP HANA. Periksa log detail di bawah.')
                    });
                } else if (r.message) {
                    let res = r.message;
                    // Update KPI Cards
                    $('#kpi-pemasukan-extracted').text(res.sap_pemasukan_extracted || 0);
                    $('#kpi-pemasukan-synced').text(res.pemasukan_synced || 0);
                    $('#kpi-pengeluaran-extracted').text(res.sap_pengeluaran_extracted || 0);
                    $('#kpi-pengeluaran-synced').text(res.pengeluaran_synced || 0);

                    // Print formatted response to console
                    append_log(`[${finish_time}] ✅ ${res.message || 'Pipeline SAP HANA selesai.'}`, '#4ade80');
                    append_log(JSON.stringify(res, null, 2), '#e2e8f0');

                    frappe.show_alert({
                        message: __('Sinkronisasi SAP HANA Selesai!'),
                        indicator: 'green'
                    }, 5);
                }
            }
        });
    }

    function append_log(text, color) {
        let log_box = $('#sap-console-log');
        let style = color ? `style="color: ${color};"` : '';
        log_box.append(`<div class="log-entry" ${style}><pre style="color: inherit; margin: 0; background: transparent; padding: 0; font-family: inherit;">${frappe.utils.escape_html(text)}</pre></div>`);
        log_box.scrollTop(log_box[0].scrollHeight);
    }
};
