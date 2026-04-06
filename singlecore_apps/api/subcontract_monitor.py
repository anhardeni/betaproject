"""
Subcontract Deadline Monitor
=============================
Early Warning System untuk dokumen subkontrak BC 2.6.1 (BC 261) yang mendekati
atau melewati tanggal jatuh tempo berdasarkan SKEP Kepala Kantor.

Logika: 
  - Hanya bekerja untuk HEADER V21 dengan kode_dokumen == '261'
  - Berpatokan pada field tgl_jatuh_tempo_subkon di Header
  - Mengirimkan email alert bertahap ke owner + role Customs/Purchasing Manager

Scheduler: daily (tiap 1 hari sekali, tengah malam)
"""

import frappe
from frappe.utils import today, date_diff, add_days, getdate, get_url, format_date


# ─── Konfigurasi Alert Threshold ──────────────────────────────────────────────
# Berapa hari sebelum jatuh tempo sistem mengirim peringatan?
ALERT_DAYS = [14, 7, 3, 0]  # H-14, H-7, H-3, Hari-H (expired)

# Role yang akan menerima email selain owner dokumen
MANAGER_ROLES = ["Customs Manager", "System Manager", "Purchasing Manager"]


# ─── Entry Point (dipanggil scheduler daily) ──────────────────────────────────
def check_subcontract_deadlines():
    """
    Fungsi utama yang dipanggil setiap hari oleh Frappe Scheduler.
    Mencari semua HEADER V21 kode 261 yang mendekati atau melewati jatuh tempo
    dan mengirimkan email notifikasi bertahap.
    """
    try:
        # Ambil semua dokumen BC 261 yang:
        # 1. Masih aktif / belum settled
        # 2. Memiliki field tgl_jatuh_tempo_subkon
        candidates = frappe.get_all(
            "HEADER V21",
            filters={
                "kode_dokumen": "261",
                "tgl_jatuh_tempo_subkon": ["is", "set"],
                # Hanya ambil yang belum settled (jika nanti field ini ada)
                # "subkon_status": ["not in", ["Settled", "Closed"]]
            },
            fields=[
                "name", "nomoraju", "owner",
                "tgl_jatuh_tempo_subkon",
                "nomor_daftar", "tanggal_daftar",
                "creation"
            ]
        )

        if not candidates:
            frappe.logger("subcontract_monitor").info("Tidak ada dokumen BC 261 aktif yang perlu dipantau.")
            return

        triggered = 0
        for doc in candidates:
            if _should_alert(doc):
                triggered += 1

        frappe.logger("subcontract_monitor").info(
            f"Subcontract Deadline Check selesai: {len(candidates)} diperiksa, {triggered} notifikasi terkirim."
        )

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Subcontract Deadline Monitor Error")


# ─── Logika Penentuan Apakah Perlu Dikirimi Alert ────────────────────────────
def _should_alert(doc):
    """
    Hitung sisa hari. Return True jika hari ini masuk dalam salah satu threshold.
    """
    jatuh_tempo = doc.get("tgl_jatuh_tempo_subkon")
    if not jatuh_tempo:
        return False

    sisa_hari = date_diff(getdate(jatuh_tempo), getdate(today()))

    # Kirim alert jika sisa hari = salah satu dari ALERT_DAYS
    # Sisa hari < 0 = sudah expired (tapi belum pernah alert hari-H)
    if sisa_hari in ALERT_DAYS or sisa_hari < 0:
        # Hindari spam: cek apakah sudah terkirim hari ini untuk sisa_hari yang sama
        if not _already_sent_today(doc["name"], sisa_hari):
            _send_deadline_alert(doc, sisa_hari)
            return True

    return False


# ─── Cek Anti Spam: Sudah Terkirim Hari Ini? ─────────────────────────────────
def _already_sent_today(header_name, sisa_hari):
    """
    Cek Comment Log di dokumen untuk menghindari pengiriman ganda dalam satu hari.
    """
    threshold_label = f"H-{sisa_hari}" if sisa_hari >= 0 else "EXPIRED"
    tag = f"[SUBKON-ALERT-{threshold_label}] {today()}"

    existing = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "HEADER V21",
            "reference_name": header_name,
            "content": ["like", f"%{tag}%"]
        },
        limit=1
    )
    return len(existing) > 0


# ─── Pengiriman Email ─────────────────────────────────────────────────────────
def _send_deadline_alert(doc, sisa_hari):
    """
    Kirim email notifikasi ke owner + manager sesuai threshold sisa hari.
    """
    header_name = doc["name"]
    no_aju = doc.get("nomoraju") or header_name
    nomor_daftar = doc.get("nomor_daftar") or "-"
    jatuh_tempo = format_date(doc.get("tgl_jatuh_tempo_subkon")) or "-"
    doc_url = get_url(f"/app/header-v21/{header_name}")

    # Tentukan level urgensi
    if sisa_hari < 0:
        level = "🔴 EXPIRED"
        urgensi_style = "background-color: #dc3545; color: white;"
        keterangan = f"Dokumen ini telah <b>melewati</b> tanggal jatuh tempo ({abs(sisa_hari)} hari yang lalu). Segera selesaikan!"
    elif sisa_hari == 0:
        level = "🔴 HARI INI JATUH TEMPO"
        urgensi_style = "background-color: #dc3545; color: white;"
        keterangan = "Dokumen ini jatuh tempo <b>HARI INI</b>. Tindakan segera diperlukan!"
    elif sisa_hari <= 3:
        level = f"🟠 H-{sisa_hari} (KRITIS)"
        urgensi_style = "background-color: #fd7e14; color: white;"
        keterangan = f"Tersisa <b>{sisa_hari} hari</b> sebelum jatuh tempo. Segera konfirmasi vendor."
    elif sisa_hari <= 7:
        level = f"🟡 H-{sisa_hari} (PERHATIAN)"
        urgensi_style = "background-color: #ffc107; color: #333;"
        keterangan = f"Tersisa <b>{sisa_hari} hari</b> sebelum jatuh tempo subkontrak."
    else:
        level = f"🟢 H-{sisa_hari} (PERINGATAN AWAL)"
        urgensi_style = "background-color: #28a745; color: white;"
        keterangan = f"Peringatan awal: Tersisa <b>{sisa_hari} hari</b> sebelum jatuh tempo."

    subject = f"[SUBKON ALERT {level}] No Aju: {no_aju}"

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 640px; margin: auto;">
        <div style="padding: 12px 20px; {urgensi_style} border-radius: 6px 6px 0 0;">
            <h2 style="margin: 0; font-size: 1.1em;">⚠️ Peringatan Jatuh Tempo Subkontrak (BC 2.6.1)</h2>
        </div>
        <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 6px 6px;">
            <p>{keterangan}</p>

            <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="background: #f8f9fa;">
                    <th style="text-align:left; padding: 8px; border: 1px solid #dee2e6; width: 35%;">Nomor Aju</th>
                    <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>{no_aju}</strong></td>
                </tr>
                <tr>
                    <th style="text-align:left; padding: 8px; border: 1px solid #dee2e6; background: #f8f9fa;">Nomor Daftar (NOPEN)</th>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">{nomor_daftar}</td>
                </tr>
                <tr style="background: #f8f9fa;">
                    <th style="text-align:left; padding: 8px; border: 1px solid #dee2e6;">Tanggal Jatuh Tempo</th>
                    <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>{jatuh_tempo}</strong></td>
                </tr>
                <tr>
                    <th style="text-align:left; padding: 8px; border: 1px solid #dee2e6; background: #f8f9fa;">Sisa Hari</th>
                    <td style="padding: 8px; border: 1px solid #dee2e6;">
                        {"<span style='color:red; font-weight:bold;'>EXPIRED (" + str(abs(sisa_hari)) + " hari)</span>" if sisa_hari < 0 else f"<strong>{sisa_hari} hari</strong>"}
                    </td>
                </tr>
            </table>

            <p style="text-align: center; margin-top: 20px;">
                <a href="{doc_url}"
                   style="background-color: #0066cc; color: white; padding: 10px 24px;
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                   📄 Lihat Dokumen HEADER V21
                </a>
            </p>
            <hr style="margin-top: 24px; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 0.8em; text-align: center;">
                Email ini dikirim otomatis oleh sistem Singlecore · {today()}
            </p>
        </div>
    </div>
    """

    # Kumpulkan penerima
    recipients = _get_recipients(doc.get("owner"))

    if not recipients:
        frappe.logger("subcontract_monitor").warning(
            f"Tidak ada email penerima untuk alert dokumen {header_name}"
        )
        return

    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=body,
            now=False  # Lewat queue/worker agar scheduler tidak berat
        )

        # Tandai di Comment Log agar tidak terkirim ganda
        threshold_label = f"H-{sisa_hari}" if sisa_hari >= 0 else "EXPIRED"
        tag = f"[SUBKON-ALERT-{threshold_label}] {today()}"
        doc_obj = frappe.get_doc("HEADER V21", header_name)
        doc_obj.add_comment(
            "Comment",
            f"{tag} — Email alert terkirim ke {len(recipients)} penerima."
        )

        frappe.logger("subcontract_monitor").info(
            f"Alert [{level}] dikirim untuk {header_name} ke {recipients}"
        )

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Gagal kirim email subkon alert: {header_name}")


# ─── Kumpulkan Daftar Penerima Email ─────────────────────────────────────────
def _get_recipients(owner):
    """
    Kumpulkan email dari: Owner dokumen + semua user yang punya role Manager.
    """
    recipients = set()

    # Owner
    if owner:
        email = frappe.db.get_value("User", owner, "email")
        if email:
            recipients.add(email)

    # Manager berdasarkan Role
    rows = frappe.get_all(
        "Has Role",
        filters={"role": ["in", MANAGER_ROLES], "parenttype": "User"},
        fields=["parent"]
    )
    for row in rows:
        email = frappe.db.get_value("User", row.parent, "email")
        if email and not email.endswith("@example.com"):  # skip dummy/system user
            recipients.add(email)

    return list(recipients)


# ─── Manual Trigger (untuk testing dari UI / bench execute) ──────────────────
@frappe.whitelist()
def manual_check():
    """
    Endpoint untuk trigger manual dari bench execute atau tombol UI.
    Contoh: bench --site dens9.com execute singlecore_apps.api.subcontract_monitor.manual_check
    """
    check_subcontract_deadlines()
    return {"status": "ok", "message": "Subcontract deadline check selesai. Lihat Error Log."}
