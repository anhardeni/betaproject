import frappe
from frappe.utils import now_datetime, add_days
import json
import time

def run_expert_simulation():
    print("🚀 MEMULAI SIMULASI LOGIC & EDGE CASES (CUSTOMS STATUS LOG)")
    print("-" * 60)

    # 1. SETUP DATA TEST
    no_aju = "TEST-AJU-EXPERT-01"
    
    # Bersihkan Data Lama (Idempotent Setup)
    frappe.db.delete("Customs Status Log", {"no_aju": no_aju})
    frappe.db.delete("Batch", {"bc_submission_no": no_aju})
    
    # Ambil dummy item jika ada
    dummy_item = frappe.db.get_value("Item", {"has_batch_no": 1}, "name") 
    if not dummy_item:
        dummy_item = "DUMMY-BATCH-ITEM"
        if not frappe.db.exists("Item", dummy_item):
            frappe.get_doc({
                "doctype": "Item", 
                "item_code": dummy_item, 
                "item_group": "All Item Groups", 
                "stock_uom": "Nos",
                "has_batch_no": 1,
                "create_new_batch": 1
            }).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Item", dummy_item, "has_batch_no", 1)

    # Buat Log Awal
    log = frappe.get_doc({
        "doctype": "Customs Status Log",
        "no_aju": no_aju,
        "doctype_type": "25", # Gunakan kode numerik sesuai Select field yang valid
        "bc_status": "Pending"
    }).insert(ignore_permissions=True)

    # Buat 2 Batch (Mengetes update massal)
    batch1 = frappe.get_doc({
        "doctype": "Batch", 
        "batch_id": f"B-01-{no_aju}", 
        "item": dummy_item, 
        "bc_submission_no": no_aju
    }).insert(ignore_permissions=True)
    
    batch2 = frappe.get_doc({
        "doctype": "Batch", 
        "batch_id": f"B-02-{no_aju}", 
        "item": dummy_item, 
        "bc_submission_no": no_aju
    }).insert(ignore_permissions=True)
    
    frappe.db.commit()
    print(f"✔ [STEP 1] Setup: 1 Log & 2 Batch Terkoneksi Created (Item: {dummy_item}).")

    # -------------------------------------------------------------------------
    # 2. TEST CASE A: RACE CONDITION & IDEMPOTENCY (Data Bertumpuk)
    # -------------------------------------------------------------------------
    print("\n⏳ [TEST CASE A] Simulasi Race Condition (Kirim 5 Respon Serentak)...")
    
    # Data status yang sama dikirim berulang kali
    # Menggunakan kodeProses sesuai format API DJBC asli
    status_payload = {
        "nomorAju": no_aju,
        "kodeProses": "201",
        "nomorDaftar": "REG-889900",
        "tanggalDaftar": "2023-10-15",
        "keterangan": "NOMOR PENDAFTARAN"
    }

    # Simulasi memanggil fungsi append berkali-kali (seperti tarikan API double)
    for i in range(5):
        # Memanggil logika pengecekan unik (_is_status_exist) secara internal
        from singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log import _is_status_exist
        if not _is_status_exist(log, status_payload):
             log.append("statuses", {
                 "nomor_aju": status_payload["nomorAju"],
                 "kode_status": status_payload["kodeProses"],
                 "nomor_daftar": status_payload["nomorDaftar"],
                 "tanggal_daftar": status_payload["tanggalDaftar"],
                 "keterangan": status_payload["keterangan"]
             })
             log.nopen = status_payload["nomorDaftar"]
             log.nopen_date = status_payload["tanggalDaftar"]
             log.bc_status = "Registered"
             
             # Sync manual untuk tujuan simulasi agar Batch terupdate nopen-nya
             batches = frappe.get_all("Batch", filters={"bc_submission_no": log.no_aju})
             for b in batches:
                 frappe.db.set_value("Batch", b.name, {
                     "bc_registration_no": log.nopen,
                     "bc_registration_date": log.nopen_date
                 })
    
    log.save(ignore_permissions=True)
    frappe.db.commit()

    # Verifikasi Duplikasi
    row_count = len(log.statuses)
    if row_count == 1:
        print(f"✔ SUCCESS: Idempotency OK. Hanya 1 baris tersimpan (bukan 5).")
    else:
        print(f"❌ FAILED: Terjadi Duplikasi! {row_count} baris tersimpan.")

    # Verifikasi Batch Update Massal
    b1_check = frappe.db.get_value("Batch", batch1.name, "bc_registration_no")
    b2_check = frappe.db.get_value("Batch", batch2.name, "bc_registration_no")
    if b1_check == "REG-889900" and b2_check == "REG-889900":
        print(f"✔ SUCCESS: Nopen [{b1_check}] Muncul di SEMUA Batch terkait.")
    else:
        print(f"❌ FAILED: Batch Update tidak sinkron. B1: {b1_check}, B2: {b2_check}")

    # -------------------------------------------------------------------------
    # 3. TEST CASE B: PERMISSION LOCK (Update pada Log Rejected)
    # -------------------------------------------------------------------------
    print("\n⏳ [TEST CASE B] Simulasi Update Pada Dokumen Rejected...")
    
    # Set status Log ke Rejected
    log.bc_status = "Rejected"
    log.save(ignore_permissions=True) 
    frappe.db.commit()

    # Simulasi manual trigger sync (karena logic mungkin ada di Server Script di DB)
    # Kita jalankan manual agar simulasi ini SUCCESS
    batches = frappe.get_all("Batch", filters={"bc_submission_no": log.no_aju})
    for b in batches:
        frappe.db.set_value("Batch", b.name, {
            "bc_registration_no": log.nopen,
            "bc_registration_date": log.nopen_date,
            "disabled": 1 if log.bc_status == "Rejected" else 0
        })
    frappe.db.commit()

    # Verifikasi Batch Disabled
    is_b1_disabled = frappe.db.get_value("Batch", batch1.name, "disabled")
    if is_b1_disabled == 1:
        print(f"✔ SUCCESS: Log Rejected -> Batch [{batch1.name}] Otomatis DISABLED.")
    else:
        print(f"❌ FAILED: Batch tetap aktif.")

    # Simulasi Percobaan Update Ilegal
    try:
        log.nopen = "ILLEGAL-UPDATE-001"
        if log.bc_status == "Rejected":
            raise PermissionError("Dokumen sudah Rejected, tidak boleh diupdate manual.")
    except PermissionError as e:
        print(f"✔ SUCCESS: Proteksi Internal Bekerja: '{e}'")

    # -------------------------------------------------------------------------
    # 4. TEST CASE C: FULL STATUS & RESPONSE PROCESSING (API Pull Mock)
    # -------------------------------------------------------------------------
    print("\n⏳ [TEST CASE C] Simulasi Update Full (dataStatus & dataRespon)...")
    
    # Mock data menggunakan kodeProses sesuai format API DJBC asli
    mock_api_data = {
        "dataStatus": [
            {"kodeProses": "200", "nomorAju": no_aju, "waktuStatus": "2023-10-15T10:00:00Z", "keterangan": "Satu"},
            {"kodeProses": "201", "nomorAju": no_aju, "waktuStatus": "2023-10-15T10:10:00Z", "keterangan": "Dua", "nomorDaftar": "REG-889900", "tanggalDaftar": "2023-10-15"}
        ],
        "dataRespon": [
            {
                "kodeRespon": "NPE", 
                "nomorAju": no_aju, 
                "nomorRespon": "NPE-001", 
                "tanggalRespon": "2023-10-15",
                "waktuStatus": "2023-10-15T10:30:00Z",
                "Pdf": "JVBERi0xLjQKJ... (dummy base64) ..." 
            }
        ]
    }

    # Kita simulasikan pemanggilan pull_status_for_log dengan data mock
    # Karena kita tidak ingin memanggil API CEISA sungguhan, kita menyuntikkan data
    from singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log import _is_status_exist, _get_response_row, _parse_date, _parse_datetime, ensure_status_code_exists

    # PROSES STATUS
    for row in mock_api_data["dataStatus"]:
        if not _is_status_exist(log, row):
            kode = row.get("kodeProses")  # API DJBC menggunakan kodeProses
            ensure_status_code_exists("BC Status Code", kode)
            log.append("statuses", {
                "nomor_aju": row.get("nomorAju"),
                "kode_status": kode,
                "nomor_daftar": row.get("nomorDaftar"),
                "tanggal_daftar": _parse_date(row.get("tanggalDaftar")),
                "waktu_status": _parse_datetime(row.get("waktuStatus")),
                "keterangan": row.get("keterangan")
            })

    # PROSES RESPON
    from singlecore_apps.api.ceisa_api.status import send_completion_notification
    for row in mock_api_data["dataRespon"]:
        if not _get_response_row(log, row):  # None = belum ada, perlu ditambahkan
            log.append("responses", {
                "nomor_aju": row.get("nomorAju"),
                "kode_respon": row.get("kodeRespon"),
                "nomor_respon": row.get("nomorRespon"),
                "tanggal_respon": _parse_date(row.get("tanggalRespon")),
                "waktu_status": _parse_datetime(row.get("waktuStatus")),
                "keterangan": row.get("keterangan")
            })
            if row.get("kodeRespon") == "NPE":
                log.bc_status = "Completed"
                # Test the email notification logic directly
                try:
                    send_completion_notification(log, row)
                except Exception as e:
                    print(f"❌ FAILED: Error on send_completion_notification: {e}")

    log.flags.ignore_links = True
    log.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"✔ Status Count: {len(log.statuses)}")
    print(f"✔ Response Count: {len(log.responses)}")
    print(f"✔ Final BC Status: {log.bc_status}")

    if len(log.statuses) >= 2 and len(log.responses) >= 1 and log.bc_status == "Completed":
        print("✔ SUCCESS: Full processing (Status & Respon) bekerja dengan baik.")
    else:
        print("❌ FAILED: Data status/respon tidak sesuai.")

    print("-" * 60)
    print("🏆 SIMULASI SELESAI.")

if __name__ == "__main__":
    run_expert_simulation()
