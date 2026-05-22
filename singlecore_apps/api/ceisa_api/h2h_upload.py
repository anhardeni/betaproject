
import json
import frappe
import requests
import os
from .auth import get_ceisa_settings, ensure_login, build_auth_headers

@frappe.whitelist()
def trigger_h2h_upload(dokumen_row_name):
    """
    Trigger H2H upload for a specific row in the DOKUMEN child table.
    Decides endpoint based on current Customs Status and document type.
    """
    try:
        row = frappe.get_doc("DOKUMEN", dokumen_row_name)
        if not row.attachment:
            return {"status": "error", "message": "File attachment is missing."}
        
        # Get Header info
        parent_doc = frappe.get_doc(row.parenttype, row.parent)
        no_aju = parent_doc.nomoraju
        npwp = frappe.db.get_value("Company", parent_doc.company, "tax_id") or "1000000000554429" # Fallback to dummy from doc
        
        # Determine Status
        bc_status = frappe.db.get_value("Customs Status Log", no_aju, "bc_status")
        
        # Determine Endpoint
        endpoint_type = "Standard"
        if bc_status == "Action Required: NPD":
            endpoint_type = "NPD"
        # Optional: check if kode_dokumen is a 'photo' category for 'Barang'
        
        frappe.db.set_value("DOKUMEN", row.name, "h2h_status", "Uploading")
        frappe.db.commit()
        
        # Execute Upload
        result = upload_to_ceisa(
            no_aju=no_aju,
            seri=row.seri or row.idx,
            npwp=npwp,
            file_url=row.attachment,
            endpoint_type=endpoint_type
        )
        
        # Update Status
        if result.get("status") == "success":
            frappe.db.set_value("DOKUMEN", row.name, {
                "h2h_status": "Success",
                "h2h_endpoint": endpoint_type,
                "h2h_upload_datetime": frappe.utils.now_datetime(),
                "h2h_error_message": ""
            })
        else:
            frappe.db.set_value("DOKUMEN", row.name, {
                "h2h_status": "Error",
                "h2h_error_message": result.get("message")
            })
        
        frappe.db.commit()
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "H2H Trigger Error")
        return {"status": "error", "message": str(e)}

def upload_to_ceisa(no_aju, seri, npwp, file_url, endpoint_type="Standard"):
    """
    Performs the actual multipart/form-data request to Beacukai OpenAPI.
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        
        endpoints = {
            "Standard": "/v2/openapi/file/dokumen",
            "Barang": "/v2/openapi/file/barang",
            "NPD": "/v2/openapi/file/upload-dokap-npd"
        }
        
        url = f"{base_url}{endpoints.get(endpoint_type, '/v2/openapi/file/dokumen')}"
        headers = build_auth_headers(token)
        # Beacukai specific: Content-Type is handled by requests for multipart
        if "Content-Type" in headers:
            del headers["Content-Type"]

        # Prepare Param
        param = {
            "nomorAju": no_aju,
            "seriDokumen": int(seri),
            "npwp": str(npwp).replace(".", "").replace("-", "")
        }
        
        # Handle File
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_content = file_doc.get_content()
        file_name = file_doc.file_name
        
        files = {
            'file': (file_name, file_content, 'application/pdf'),
            'param': (None, json.dumps(param))
        }

        response = requests.post(url, headers=headers, files=files, timeout=(10, 30))
        
        if response.status_code in [200, 201]:
            return {"status": "success", "data": response.json()}
        else:
            return {
                "status": "error", 
                "message": f"API Error {response.status_code}: {response.text}",
                "url": url
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CEISA H2H Upload Core Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def trigger_h2h_barang_upload(barang_name):
    """
    Trigger H2H photo upload for a BARANG V1 document.
    Sends product image to Beacukai.
    """
    try:
        row = frappe.get_doc("BARANG V1", barang_name)
        if not row.gambar_barang:
            return {"status": "error", "message": "Product image (gambar_barang) is missing."}
        
        # Get Header info
        parent_doc = frappe.get_doc("HEADER V21", row.nomoraju)
        no_aju = parent_doc.nomoraju
        npwp = frappe.db.get_value("Company", parent_doc.company, "tax_id") or "1000000000554429"
        
        frappe.db.set_value("BARANG V1", row.name, "h2h_status", "Uploading")
        frappe.db.commit()
        
        # Execute Upload
        result = upload_barang_photo_to_ceisa(
            no_aju=no_aju,
            seri=row.seri_barang or 1,
            npwp=npwp,
            file_url=row.gambar_barang,
            keterangan=row.uraian or "gambar"
        )
        
        # Update Status
        if result.get("status") == "success":
            frappe.db.set_value("BARANG V1", row.name, {
                "h2h_status": "Success",
                "h2h_upload_datetime": frappe.utils.now_datetime(),
                "h2h_error_message": ""
            })
        else:
            frappe.db.set_value("BARANG V1", row.name, {
                "h2h_status": "Error",
                "h2h_error_message": result.get("message")
            })
        
        frappe.db.commit()
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "H2H Barang Upload Trigger Error")
        return {"status": "error", "message": str(e)}


def upload_barang_photo_to_ceisa(no_aju, seri, npwp, file_url, keterangan):
    """
    Performs the physical photo/image upload to Beacukai OpenAPI.
    """
    try:
        token = ensure_login()
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        
        url = f"{base_url}/v2/openapi/file/barang"
        headers = build_auth_headers(token)
        if "Content-Type" in headers:
            del headers["Content-Type"]

        # Prepare Param
        param = {
            "keterangan": str(keterangan)[:50],
            "nomorAju": no_aju,
            "seriBarang": int(seri),
            "npwp": str(npwp).replace(".", "").replace("-", "")
        }
        
        # Handle File
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_content = file_doc.get_content()
        file_name = file_doc.file_name
        
        # Determine mime type
        ext = os.path.splitext(file_name)[1].lower()
        mime_type = "image/jpeg"
        if ext == ".png":
            mime_type = "image/png"
        elif ext == ".pdf":
            mime_type = "application/pdf"
            
        files = {
            'file': (file_name, file_content, mime_type),
            'param': (None, json.dumps(param))
        }

        response = requests.post(url, headers=headers, files=files, timeout=(10, 30))
        
        if response.status_code in [200, 201]:
            return {"status": "success", "data": response.json()}
        else:
            return {
                "status": "error", 
                "message": f"API Error {response.status_code}: {response.text}",
                "url": url
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CEISA H2H Barang Upload Core Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def reload_h2h_schemas():
    """
    Reload DOKUMEN and BARANG V1 schemas and update database columns.
    """
    frappe.reload_doc("singlecore_apps", "doctype", "dokumen", force=True)
    frappe.db.updatedb("DOKUMEN")
    frappe.reload_doc("singlecore_apps", "doctype", "barang_v1", force=True)
    frappe.db.updatedb("BARANG V1")
    frappe.db.commit()
    return {"status": "success", "message": "Schemas reloaded successfully."}
