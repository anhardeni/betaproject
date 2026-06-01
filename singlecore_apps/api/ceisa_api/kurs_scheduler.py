# -*- coding: utf-8 -*-
# File: kurs_scheduler.py
# Deskripsi: Otomatisasi penarikan Kurs KMK mingguan (Rabu) dari CEISA API 
#            dan sinkronisasi ke database Currency Exchange ERPNext.

import frappe
from .kurs import get_kurs

def fetch_and_update_ceisa_kurs():
    """
    Scheduler mingguan otomatis (dijalankan setiap hari Rabu jam 00.05 WIB).
    Menarik Kurs KMK terbaru untuk USD dari CEISA dan memperbarui Currency Exchange ERPNext.
    """
    try:
        # Panggil API CEISA untuk mata uang USD (Kurs KMK Acuan Utama)
        res = get_kurs("USD")
        if res.get("status") == "success":
            data_ceisa = res.get("data", {})
            
            # CEISA mengembalikan data berbentuk bersarang, parse datanya
            rows = []
            if isinstance(data_ceisa, dict):
                rows = data_ceisa.get("data", [])
            
            if rows and len(rows) > 0:
                nilai_kurs = rows[0].get("nilaiKurs")
                if nilai_kurs:
                    rate = float(nilai_kurs)
                    today = frappe.utils.today()
                    
                    # Cek apakah entri Currency Exchange untuk hari ini sudah ada
                    exchange_rate_name = frappe.db.get_value(
                        "Currency Exchange",
                        {
                            "from_currency": "USD",
                            "to_currency": "IDR",
                            "date": today,
                            "for_buying": 1,
                            "for_selling": 1
                        },
                        "name"
                    )
                    
                    if exchange_rate_name:
                        # Jika sudah ada entri, update nilainya
                        frappe.db.set_value("Currency Exchange", exchange_rate_name, "exchange_rate", rate)
                    else:
                        # Jika belum ada entri, buat baru
                        ce = frappe.get_doc({
                            "doctype": "Currency Exchange",
                            "from_currency": "USD",
                            "to_currency": "IDR",
                            "date": today,
                            "exchange_rate": rate,
                            "for_buying": 1,
                            "for_selling": 1
                        })
                        ce.insert(ignore_permissions=True)
                    
                    frappe.db.commit()
                    frappe.logger("ceisa_api").info(f"Otomatisasi Kurs KMK: Berhasil memperbarui kurs USD ke IDR senilai {rate} pada tanggal {today}.")
                else:
                    frappe.logger("ceisa_api").warning("Otomatisasi Kurs KMK: Gagal, nilaiKurs tidak ditemukan di respon API.")
            else:
                frappe.logger("ceisa_api").warning("Otomatisasi Kurs KMK: Gagal, data list kosong di respon CEISA.")
        else:
            frappe.logger("ceisa_api").error(f"Otomatisasi Kurs KMK Gagal: {res.get('message')}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Otomatisasi Kurs KMK Scheduler Error")
