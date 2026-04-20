"""
CEISA Status & Respon API
=========================

Check document status/response from CEISA API.

Endpoints:
    - GET /openapi/status/{nomorAju}              - Status by Nomor Aju
    - GET /openapi/status?idPerusahaan={npwp}     - Status by NPWP
    - GET /openapi/download-respon/{path}         - Download response file
    - GET /openapi/respon/cetak-formulir/{nomorAju} - Cetak formulir respon
"""

import frappe
import requests
from .auth import get_ceisa_settings, ensure_login, build_auth_headers


@frappe.whitelist()
def get_status_by_nomor_aju(nomor_aju):
    """Get CEISA document status/response by Nomor Aju.

    Endpoint: GET /openapi/status/{nomorAju}
    Requires: Bearer token

    Args:
        nomor_aju: Nomor Aju dokumen pabean (26 digit)

    Returns:
        dict with status response data
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/status/{nomor_aju}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by Nomor Aju Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by Nomor Aju Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_status_by_npwp(npwp):
    """Get CEISA document status/response by NPWP perusahaan.

    Endpoint: GET /openapi/status?idPerusahaan={npwp}
    Requires: Bearer token

    Args:
        npwp: NPWP perusahaan (15 digit)

    Returns:
        dict with list of document statuses for the company
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/status"
        headers = build_auth_headers(token)
        params = {"idPerusahaan": npwp}

        response = requests.get(url, headers=headers, params=params)

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": response.json() if response.content else response.text
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by NPWP Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by NPWP Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def download_respon(path):
    """Download response file from CEISA API.

    Endpoint: GET /openapi/download-respon/{path}
    Requires: Bearer token

    The 'path' parameter is obtained from the response of
    get_status_by_nomor_aju() or get_status_by_npwp().

    Args:
        path: File path from status response

    Returns:
        dict with downloaded response data
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/download-respon/{path}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        # Try to parse as JSON, fallback to raw text
        try:
            data = response.json()
        except Exception:
            data = response.text

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": data
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Download Respon Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Download Respon Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def cetak_formulir(nomor_aju):
    """Cetak formulir respon dokumen pabean.

    Endpoint: GET /openapi/respon/cetak-formulir/{nomorAju}
    Requires: Bearer token

    Args:
        nomor_aju: Nomor Aju dokumen pabean (26 digit)

    Returns:
        dict with formulir data (PDF or response content)
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/respon/cetak-formulir/{nomor_aju}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)

        # Try to parse as JSON, fallback to raw content
        try:
            data = response.json()
        except Exception:
            data = response.text

        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "data": data
        }

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Cetak Formulir Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cetak Formulir Error")
        return {"status": "error", "message": str(e)}

def send_completion_notification(log, response):
    """
    Mengirimkan email notifikasi ke Pembuat (Owner) dokumen dan Manajer
    ketika dokumen menerima respon SPPB atau NPE.
    
    Args:
        log (Document): Objek Customs Status Log
        response (dict/str): Baris respon terakhir dari CEISA
    """
    # 1. Menyiapkan Data Dokumen
    no_aju = log.no_aju
    nomor_daftar = response.get("nomorDaftar") or log.nopen
    waktu_respon = response.get("waktuRespon")
    kode_respon = response.get("kodeRespon")
    keterangan = response.get("keterangan") or "Selesai"
    
    # 2. Mendapatkan URL Dokumen untuk link (Memudahkan user langsung klik)
    from frappe.utils import get_url
    doc_link = get_url(f"/app/customs-status-log/{log.name}")
    
    # 3. Mendapatkan Daftar Email Penerima
    recipients = []
    
    # A. Email Pembuat (Owner)
    owner_email = frappe.db.get_value("User", log.owner, "email")
    if owner_email:
        recipients.append(owner_email)
        
    # B. Email Manajer (Optimal Decision: Ambil dari Role tertentu)
    # Contoh: Mengirim ke semua user yang memiliki role "System Manager" atau "Customs Manager"
    manager_roles = ["System Manager", "Customs Manager"] # Sesuaikan dengan Role di perusahaan Anda
    managers = frappe.get_all("Has Role", 
        filters={"role": ["in", manager_roles], "parenttype": "User"}, 
        fields=["parent"]
    )
    
    for mgr in managers:
        mgr_email = frappe.db.get_value("User", mgr.parent, "email")
        if mgr_email and mgr_email not in recipients:
            recipients.append(mgr_email)
            
    # Jika tidak ada email satupun yang ditemukan, hentikan fungsi
    if not recipients:
        frappe.logger("customs_status_log").warning(f"Tidak ada email penerima untuk notifikasi Aju {no_aju}")
        return
    # 4. Menyusun Template Email (HTML)
    subject = f"Pemberitahuan: Respon {kode_respon} untuk No Aju {no_aju}"
    
    message = f"""
    <h3>Pemberitahuan Status Dokumen Bea Cukai</h3>
    <p>Dokumen Anda telah menerima respon akhir (<b>{kode_respon}</b>) dari sistem CEISA.</p>
    
    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr>
            <th style="background-color: #f8f9fa; text-align: left; width: 30%;">Nomor Aju</th>
            <td>{no_aju}</td>
        </tr>
        <tr>
            <th style="background-color: #f8f9fa; text-align: left;">Nomor Daftar</th>
            <td>{nomor_daftar}</td>
        </tr>
        <tr>
            <th style="background-color: #f8f9fa; text-align: left;">Respon</th>
            <td><strong>{kode_respon}</strong> - {keterangan}</td>
        </tr>
        <tr>
            <th style="background-color: #f8f9fa; text-align: left;">Waktu Respon</th>
            <td>{waktu_respon}</td>
        </tr>
    </table>
    
    <br>
    <p>Silakan klik tombol di bawah ini untuk melihat detail dokumen (dan mendownload file PDF jika tersedia):</p>
    <a href="{doc_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Lihat Dokumen di ERPNext</a>
    <br><br>
    <p><i>Email ini dikirim secara otomatis oleh sistem.</i></p>
    """
    # 5. Menyiapkan Lampiran (Attachment) PDF jika ada
    attachments = []
    pdf_link = response.get("pdf_file")
    if pdf_link:
        # Menambahkan URL file lokal ke dalam daftar lampiran email frappe
        attachments.append({"file_url": pdf_link})
    # 6. Mengambil Email Pengirim dari Profil Perusahaan (Jika di-set)
    sender_email = None
    if log.get("company"):
        company_email = frappe.db.get_value("Company", log.get("company"), "email")
        if company_email:
            sender_email = company_email
    # 7. Mengirim Email (Gunakan background worker agar API stabil)
    frappe.sendmail(
        sender=sender_email, # Akan menggunakan email sistem default jika ini None
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=attachments,
        now=False
    )
    
    frappe.logger("customs_status_log").info(f"Email notifikasi {kode_respon} dikirim ke {len(recipients)} penerima untuk Aju {no_aju}")
    log.add_comment("Comment", f"Notifikasi email {kode_respon} telah dikirimkan secara otomatis.")

