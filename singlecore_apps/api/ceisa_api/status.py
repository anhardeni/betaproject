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
    """Get CEISA document status/response by Nomor Aju."""
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
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by Nomor Aju Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_status_by_npwp(npwp):
    """Get CEISA document status/response by NPWP perusahaan."""
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
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Status by NPWP Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def download_respon(path):
    """
    Download binary response from CEISA.
    Attempts multiple URL patterns and both Authenticated/Unauthenticated modes.
    """
    try:
        from .auth import ensure_login, build_auth_headers
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        # Multi-check pola URL
        patterns = [
            f"{base_url}/openapi/download-respon?path={path}",
            f"{base_url}/openapi/{path}",
            f"{base_url}/{path}",
        ]
        
        last_error_info = ""
        
        # Coba tiap pola dengan 2 kondisi: Pakai Token & Tanpa Token
        for url in patterns:
            for use_token in [True, False]:
                try:
                    headers = build_auth_headers(token if use_token else None)
                    if "?" in url:
                        base, query = url.split("?", 1)
                        p_name, p_val = query.split("=", 1)
                        r = requests.get(base, params={p_name: p_val}, headers=headers, timeout=10)
                    else:
                        r = requests.get(url, headers=headers, timeout=10)
                    
                    if r.status_code == 200:
                        # Success case
                        return {
                            "status": "success",
                            "data": r.content,
                            "url": r.url,
                            "mode": "Token" if use_token else "API-Key Only"
                        }
                    else:
                        # Log but continue
                        last_error_info = f"URL: {url} | Status: {r.status_code} | Mode: {'Token' if use_token else 'API-Key'}"
                except Exception as e:
                    last_error_info = f"URL: {url} | Exception: {str(e)}"
                    continue

        # If we reach here, all failed
        return {
            "status": "error",
            "message": f"Download Gagal. Terakhir: {last_error_info}"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "download_respon System Error")
        return {"status": "error", "message": f"System Error: {str(e)}"}


def send_completion_notification(log_doc, api_row):
    """
    Kirim email notifikasi jika status SPPB/NPE tercapai.
    Attachment: PDF yang barusan didownload.
    """
    try:
        # Tentukan recipient (bisa dari setting atau owner dokumen)
        settings = get_ceisa_settings()
        recipient = settings.notification_email or log_doc.owner
        
        if not recipient or recipient == "Administrator":
            # Fallback ke email user yang sedang aktif jika administrator
            recipient = frappe.session.user
            
        if not recipient or "@" not in recipient:
            frappe.logger("ceisa_api").warning("Email skip: No valid recipient found.")
            return

        kode = api_row.get("kodeRespon") or "RESPON"
        no_aju = log_doc.nomor_aju
        pdf_file = api_row.get("pdf_file") # Ini adalah file path (id File)

        subject = f"NOTIFIKASI CEISA: {kode} - {no_aju}"
        message = f"""
        <p>Halo,</p>
        <p>Dokumen dengan Nomor Aju <b>{no_aju}</b> telah mendapatkan respon <b>{kode}</b> dari Bea Cukai.</p>
        <p>Terlampir adalah dokumen PDF respon tersebut.</p>
        <br>
        <p>Salam,<br>Sistem CEISA Auto-Sync</p>
        """

        attachments = []
        if pdf_file:
            # pdf_file di sini adalah nama dokumen 'File' di Frappe (misal: "private/files/...")
            # Kita perlu mendapatkan path aslinya
            file_doc = frappe.get_doc("File", pdf_file)
            attachments.append({
                "fname": file_doc.file_name,
                "fcontent": file_doc.get_content()
            })

        frappe.sendmail(
            recipients=[recipient],
            subject=subject,
            content=message,
            attachments=attachments
            if attachments else None
        )
        
        frappe.logger("ceisa_api").info(f"Email notifikasi dikirim ke {recipient}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Notification Error")
