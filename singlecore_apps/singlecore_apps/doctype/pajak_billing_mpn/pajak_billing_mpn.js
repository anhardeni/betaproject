// Copyright (c) 2026, AnharDeni and contributors
// For license information, please see license.txt

// File: pajak_billing_mpn.js
// Deskripsi: Menambahkan tombol eksekusi API, proteksi Dual-Approval (Maker-Checker),
//            validasi OTP via Email, kalkulasi otomatis, dan form locking keamanan.

frappe.ui.form.on('Pajak Billing MPN', {
    refresh: function (frm) {
        // 1. Tampilkan/Sembunyikan kolom khusus transaksi QQ
        frm.trigger('is_qq_transaction');
        
        // 2. [PROTEKSI DATA TAMPERING]
        // Kunci dokumen secara mutlak jika sudah disetujui (Approved) atau sudah dibayar (Paid)
        if (frm.doc.approval_status === 'Approved' || frm.doc.approval_status === 'Paid') {
            frm.disable_form(); // Membuat seluruh field menjadi Read-Only secara instan
        }
        
        // 3. Tombol-Tombol Alur Otorisasi (Maker-Checker)
        if (!frm.is_new()) {
            
            // TAHAP 1: Approval Checker (Finance Manager menyetujui pengajuan)
            if (frm.doc.approval_status === 'Draft') {
                
                // Pastikan hanya user berwenang (Finance Manager / System Manager) yang memiliki akses
                if (frappe.user.has_role('Finance Manager') || frappe.user.has_role('System Manager') || frappe.user.has_role('Accounts Manager')) {
                    
                    frm.add_custom_button(__('Setujui Pengajuan Pembayaran'), function () {
                        frappe.confirm(
                            __('Apakah Anda yakin menyetujui pengajuan pelunasan billing Bea Cukai {0} sebesar Rp {1}? Dokumen akan dikunci setelah disetujui.', 
                            [frm.doc.kode_billing, format_currency(frm.doc.jumlah_bayar)]),
                            function () {
                                frappe.call({
                                    method: 'singlecore_apps.api.briapi_mpn_integration.approve_payment_proposal',
                                    args: { docname: frm.doc.name },
                                    freeze: true,
                                    freeze_message: __('Menyetujui Pengajuan...'),
                                    callback: function (r) {
                                        if (r.message && r.message.status === 'Sukses') {
                                            frappe.show_alert({
                                                message: __('Persetujuan berhasil disimpan. Dokumen terkunci.'),
                                                indicator: 'green'
                                            });
                                            frm.reload_doc();
                                        }
                                    }
                                });
                            }
                        );
                    }).addClass('btn-success'); // Warna hijau menandakan persetujuan
                }
                
            } 
            
            // TAHAP 2: Eksekusi Pembayaran API oleh Checker (Wajib validasi OTP via Email)
            else if (frm.doc.approval_status === 'Approved' && frm.doc.status_pembayaran !== 'Berhasil') {
                
                frm.add_custom_button(__('Bayar Pajak via BRIAPI'), function () {
                    // Panggil backend terlebih dahulu untuk membuat dan mengirimkan OTP ke email approver
                    frappe.call({
                        method: 'singlecore_apps.api.briapi_mpn_integration.request_otp',
                        args: { docname: frm.doc.name },
                        freeze: true,
                        freeze_message: __('Mengirimkan Kode OTP Keamanan ke Email...'),
                        callback: function (r) {
                            if (r.message && r.message.status === 'Sukses') {
                                frappe.show_alert({
                                    message: __('Kode OTP keamanan terkirim.'),
                                    indicator: 'blue'
                                });
                                // Munculkan popup dialog interaktif pengisian OTP
                                show_otp_dialog(frm);
                            } else {
                                frappe.msgprint({
                                    title: __('Gagal Mengirim OTP'),
                                    indicator: 'red',
                                    message: r.message ? r.message.error : __('Terjadi kesalahan sistem pengiriman email.')
                                });
                            }
                        }
                    });
                }).addClass('btn-primary'); // Warna biru dominan untuk tombol eksekusi dana
                
            }
        }
    },
    
    is_qq_transaction: function (frm) {
        // Logika menyembunyikan / menampilkan field khusus Impor QQ secara dinamis
        if (frm.doc.is_qq_transaction) {
            frm.set_df_property('customer', 'reqd', 1);
            frm.set_df_property('customer', 'hidden', 0);
            frm.set_df_property('npwp_qq', 'reqd', 1);
            frm.set_df_property('npwp_qq', 'hidden', 0);
        } else {
            frm.set_df_property('customer', 'reqd', 0);
            frm.set_df_property('customer', 'hidden', 1);
            frm.set_df_property('npwp_qq', 'reqd', 0);
            frm.set_df_property('npwp_qq', 'hidden', 1);
            frm.set_value('customer', '');
            frm.set_value('npwp_qq', '');
        }
    }
});

// 4. [KALKULATOR NOMINAL LIVE]
// Memicu perhitungan akumulasi otomatis setiap kali tabel anak 'rincian_pajak' mengalami perubahan
frappe.ui.form.on('Pajak Billing Detail', {
    amount: function (frm, cdt, cdn) {
        calculate_total_pajak(frm);
    },
    rincian_pajak_add: function (frm, cdt, cdn) {
        calculate_total_pajak(frm);
    },
    rincian_pajak_remove: function (frm, cdt, cdn) {
        calculate_total_pajak(frm);
    }
});

function calculate_total_pajak(frm) {
    let total = 0.0;
    if (frm.doc.rincian_pajak) {
        frm.doc.rincian_pajak.forEach(row => {
            total += flt(row.amount);
        });
    }
    frm.set_value('jumlah_bayar', total);
}

// 5. [INTERACTIVE OTP POPUP DIALOG]
function show_otp_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Verifikasi Keamanan OTP'),
        fields: [
            {
                fieldname: 'info_html',
                fieldtype: 'HTML',
                options: `
                    <div style="background-color: #f1f5f9; border-left: 4px solid #003366; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
                        <p style="margin: 0; font-size: 13px; color: #333; line-height: 1.5;">
                            Kode keamanan OTP 6-Digit telah dikirim ke email Approver Utama terdaftar. 
                            Harap masukkan kode di bawah ini untuk mengonfirmasi penarikan dana riil bank Anda.
                        </p>
                    </div>
                `
            },
            {
                label: __('Masukkan Kode OTP'),
                fieldname: 'otp_input',
                fieldtype: 'Data',
                reqd: 1,
                description: __('Masa aktif kode OTP adalah 5 menit')
            }
        ],
        primary_action_label: __('Konfirmasi & Bayar'),
        primary_action(values) {
            d.hide();
            
            // Jalankan API eksekusi pembayaran riil dengan OTP
            frappe.call({
                method: 'singlecore_apps.api.briapi_mpn_integration.execute_payment_otp',
                args: {
                    docname: frm.doc.name,
                    otp: values.otp_input
                },
                freeze: true,
                freeze_message: __('Menghubungkan ke Server Bank & Mengeksekusi Transfer...'),
                callback: function (r) {
                    if (r.message && r.message.status === 'Sukses') {
                        frappe.show_alert({
                            message: __('Pembayaran Berhasil! NTPN: ') + r.message.ntpn,
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('Gagal Memproses Pembayaran'),
                            indicator: 'red',
                            message: r.message ? r.message.error : (r.message && r.message.warning ? r.message.warning : __('Terjadi kesalahan tak terduga.'))
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    });
    
    // Fitur Kirim Ulang OTP jika manajer keuangan belum menerima email
    d.set_secondary_action_label(__('Kirim Ulang OTP'));
    d.set_secondary_action(() => {
        d.hide();
        // Trigger ulang pemanggilan pengiriman email OTP
        frm.trigger('refresh');
    });
    
    d.show();
}
