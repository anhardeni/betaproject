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

        #response = requests.get(url, headers=headers)
        response = requests.get(url, headers=headers, timeout=(5, 15))

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

        #response = requests.get(url, headers=headers, params=params)
        response = requests.get(url, headers=headers, params=params, timeout=(5, 15))


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
        
        # Di background worker, frappe.session.user sering kali adalah "Administrator" atau None.
        # Kita perlu mencari user yang berhak menerima email atau fallback logis yang valid.
        if not recipient or recipient == "Administrator":
            # Cari user terakhir yang memodifikasi dokumen atau pemilik asli
            recipient = log_doc.modified_by or log_doc.owner
            if not recipient or recipient == "Administrator":
                # Fallback terakhir ke user aktif (jika ada) atau cari System Manager pertama
                recipient = frappe.session.user
                if not recipient or recipient == "Administrator":
                    system_managers = frappe.get_all("User", filters={"enabled": 1}, fields=["email"])
                    # Cari yang bukan Administrator
                    for u in system_managers:
                        if u.email and u.email != "Administrator" and "@" in u.email:
                            recipient = u.email
                            break

        if not recipient or "@" not in recipient:
            frappe.logger("ceisa_api").warning("Email skip: No valid recipient found.")
            return

        kode = api_row.get("kodeRespon") or "RESPON"
        no_aju = log_doc.no_aju
        pdf_file = api_row.get("pdf_file") # Ini adalah file path atau name (ID File)

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
            # pdf_file di sini bisa berupa name/ID dokumen 'File' (misal: "FL00001")
            # atau langsung berupa URL/path (misal: "/private/files/...")
            file_doc = None
            if frappe.db.exists("File", pdf_file):
                file_doc = frappe.get_doc("File", pdf_file)
            else:
                # Jika pdf_file berupa path, coba cari berdasarkan file_url atau file_name
                file_name_db = frappe.db.get_value("File", {"file_url": pdf_file}, "name")
                if not file_name_db:
                    file_name_db = frappe.db.get_value("File", {"file_name": pdf_file.split("/")[-1]}, "name")
                
                if file_name_db:
                    file_doc = frappe.get_doc("File", file_name_db)

            if file_doc:
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

        row_name = api_row.get("name")
        if row_name:
            frappe.db.set_value("Customs Status Log Response", row_name, "is_email_sent", 1, update_modified=False)
            frappe.db.commit()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Notification Error")


@frappe.whitelist()
def cetak_formulir(nomor_aju):
    """
    Cetak formulir respon dari CEISA.
    Shortcut ke endpoint /openapi/respon/cetak-formulir/{nomor_aju}
    """
    try:
        from .auth import ensure_login, build_auth_headers
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"

        url = f"{base_url}/openapi/respon/cetak-formulir/{nomor_aju}"
        headers = build_auth_headers(token)

        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return {
                "status": "success",
                "data": response.content if "pdf" in response.headers.get("Content-Type", "") else response.json()
            }
        else:
            return {"status": "error", "message": f"Cetak gagal: {response.status_code}"}
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Cetak Formulir Error")
        return {"status": "error", "message": str(e)}


def _get_or_download_pdf(nomor_aju, file_prefix, api_endpoint, params=None):
    """Central cache manager helper that gets locally cached PDF or downloads it from CEISA API."""
    try:
        file_name = f"CEISA_{nomor_aju}_{file_prefix}.pdf"
        
        # 1. Cache hit check: Look up existing private file attachment linked to the parent document
        cached_file_url = frappe.db.get_value(
            "File",
            {
                "attached_to_doctype": "Customs Status Log",
                "attached_to_name": nomor_aju,
                "file_name": ["like", f"CEISA_{nomor_aju}_{file_prefix}%.pdf"]
            },
            "file_url"
        )
        if cached_file_url:
            return {"status": "success", "data": cached_file_url}
            
        # 2. Cache miss: Request PDF from CEISA API
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        url = f"{base_url}{api_endpoint}"
        headers = build_auth_headers(token)
        
        response = requests.get(url, headers=headers, params=params, timeout=(10, 30))
        
        # Handle 401 token refresh once
        if response.status_code == 401:
            from .auth import refresh_token
            new_token = refresh_token()
            if new_token:
                headers = build_auth_headers(new_token)
                response = requests.get(url, headers=headers, params=params, timeout=(10, 30))
                
        if response.status_code == 200:
            # 3. Create private local file attachment in Frappe file manager
            from frappe.utils.file_manager import save_file
            file_doc = save_file(
                fname=file_name,
                content=response.content,
                dt="Customs Status Log",
                dn=nomor_aju,
                is_private=1
            )
            return {"status": "success", "data": file_doc.file_url}
        else:
            error_msg = f"Download failed: HTTP {response.status_code} - {response.text}"
            frappe.log_error(title="CEISA PDF Cache Helper Error", message=error_msg)
            return {"status": "error", "message": error_msg}
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CEISA PDF Cache Helper System Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_cetak_formulir_draft(nomor_aju):
    """Retrieve Draft Formulir PDF by Nomor Aju (utilizing local hybrid caching)."""
    return _get_or_download_pdf(
        nomor_aju=nomor_aju,
        file_prefix="draft",
        api_endpoint="/openapi/respon/cetak-formulir",
        params={"nomorAju": nomor_aju}
    )


@frappe.whitelist()
def get_cetak_formulir_final(nomor_aju):
    """Retrieve Final Formulir PDF by Nomor Aju (utilizing local hybrid caching)."""
    return _get_or_download_pdf(
        nomor_aju=nomor_aju,
        file_prefix="final",
        api_endpoint="/openapi/respon/cetak-formulir",
        params={"nomorAju": nomor_aju}
    )


@frappe.whitelist()
def get_active_billing_code(nomor_aju):
    """Scan response logs for a given nomor_aju and return the first detected billing code."""
    try:
        import json
        import re
        
        # Find all responses linked to the nomor_aju
        responses = frappe.get_all(
            "Customs Status Log Response",
            filters={"nomor_aju": nomor_aju},
            fields=["keterangan", "pesan_json"]
        )
        
        # Compile a regex for 15-digit numeric string
        billing_regex = re.compile(r"\b\d{15}\b")
        
        # Check in each response record
        for r in responses:
            # 1. Check in keterangan field
            if r.keterangan:
                match = billing_regex.search(r.keterangan)
                if match:
                    return {"status": "success", "billing_code": match.group(0)}
                    
            # 2. Check in pesan_json field
            if r.pesan_json:
                # Direct regex search on the raw JSON string first
                match = billing_regex.search(r.pesan_json)
                if match:
                    return {"status": "success", "billing_code": match.group(0)}
                
                # Nested JSON key-value parse search
                try:
                    data = json.loads(r.pesan_json)
                    detected = _scan_json_for_billing(data)
                    if detected:
                        return {"status": "success", "billing_code": detected}
                except Exception:
                    pass
                    
        return {"status": "success", "billing_code": None}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Active Billing Code Error")
        return {"status": "error", "message": str(e)}


def _scan_json_for_billing(obj):
    """Helper to recursively scan JSON objects for billing codes."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            # Check key names
            if k.lower() in ["kodebilling", "kode_billing", "billingcode", "billing_code"]:
                if isinstance(v, str) and v.strip().isdigit() and len(v.strip()) == 15:
                    return v.strip()
                elif isinstance(v, (int, float)):
                    s = str(v)
                    if len(s) == 15:
                        return s
            
            # Recurse
            res = _scan_json_for_billing(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = _scan_json_for_billing(item)
            if res:
                return res
    elif isinstance(obj, str):
        # Check if the string itself is a 15-digit number
        s = obj.strip()
        if s.isdigit() and len(s) == 15:
            return s
    return None


@frappe.whitelist()
def get_billing_pdf(nomor_aju, billing_code):
    """Retrieve Billing PDF by Nomor Aju and Billing Code (utilizing local hybrid caching)."""
    return _get_or_download_pdf(
        nomor_aju=nomor_aju,
        file_prefix="billing",
        api_endpoint=f"/openapi/respon/billing/{billing_code}"
    )


@frappe.whitelist()
def get_active_responses(nomor_aju):
    """Return all active responses for a given nomor_aju, including their local caching state."""
    try:
        responses = frappe.get_all(
            "Customs Status Log Response",
            filters={"nomor_aju": nomor_aju},
            fields=["name", "kode_respon", "tanggal_respon", "waktu_respon", "keterangan", "pdf_file"]
        )
        
        for r in responses:
            r.is_cached = 0
            r.file_url = None
            
            # 1. If pdf_file link is already set, fetch its url
            if r.pdf_file:
                file_url = frappe.db.get_value("File", r.pdf_file, "file_url")
                if file_url:
                    r.is_cached = 1
                    r.file_url = file_url
                    continue
            
            # 2. Check if a cached private file exists matching the prefix
            prefix = r.kode_respon.lower()
            cached_file_url = frappe.db.get_value(
                "File",
                {
                    "attached_to_doctype": "Customs Status Log",
                    "attached_to_name": nomor_aju,
                    "file_name": ["like", f"CEISA_{nomor_aju}_{prefix}%.pdf"]
                },
                "file_url"
            )
            if cached_file_url:
                r.is_cached = 1
                r.file_url = cached_file_url
                # Update pdf_file link in DB for future lookup
                file_name = frappe.db.get_value("File", {"file_url": cached_file_url}, "name")
                if file_name:
                    frappe.db.set_value("Customs Status Log Response", r.name, "pdf_file", file_name, update_modified=False)
                    frappe.db.commit()
                    
        return {"status": "success", "data": responses}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Active Responses Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_response_pdf(nomor_aju, kode_respon):
    """Retrieve general Response PDF (e.g. SPPB, NPE) by Nomor Aju and Kode Respon (utilizing local hybrid caching)."""
    prefix = kode_respon.lower()
    return _get_or_download_pdf(
        nomor_aju=nomor_aju,
        file_prefix=prefix,
        api_endpoint="/openapi/respon/pdf",
        params={"nomorAju": nomor_aju, "kodeRespon": kode_respon}
    )




