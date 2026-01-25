import frappe
import requests
from . import ceisa_export

BEACUKAI_BASE_URL = "https://apis-gw.beacukai.go.id"

def get_cached_token():
    return frappe.cache().hget("beacukai_token", frappe.session.user)

@frappe.whitelist()
def login_beacukai(username, password):
    url = f"{BEACUKAI_BASE_URL}/nle-oauth/v1/user/login"
    payload = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        token = None
        if "item" in data and "access_token" in data["item"]:
             token = data["item"]["access_token"]
        elif "access_token" in data:
             token = data["access_token"]
        
        if token:
            frappe.cache().hset("beacukai_token", frappe.session.user, token)
            return {"status": "success", "message": "Login successful"}
        else:
            return {"status": "error", "message": "Token not found", "response": data}
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Beacukai Login Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def check_ceisa_status(nomor_aju):
    token = get_cached_token()
    if not token:
        return {"status": "error", "message": "Please login to Beacukai first."}
        
    url = f"{BEACUKAI_BASE_URL}/openapi/status/{nomor_aju}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "response": response.json() if response.content else response.text
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def send_ceisa_document(docname):
    """Dynamically sends the correct CEISA document based on kode_dokumen"""
    token = get_cached_token()
    if not token:
        return {"status": "error", "message": "Please login to Beacukai first."}
    
    try:
        # Get the document to determine its type
        doc = frappe.get_doc("HEADER V21", docname)
        bc_type = doc.kode_dokumen
        
        # Mapping of document codes to their export functions
        EXPORT_MAP = {
            "16": ceisa_export.get_ceisa_bc16_json,
            "20": ceisa_export.get_ceisa_bc20_json,
            "23": ceisa_export.get_ceisa_bc23_json,
            "25": ceisa_export.get_ceisa_bc25_json,
            "27": ceisa_export.get_ceisa_bc27_json,
            "28": ceisa_export.get_ceisa_bc28_json,
            "30": ceisa_export.get_ceisa_bc30_json,
            "33": ceisa_export.get_ceisa_bc33_json,
            "40": ceisa_export.get_ceisa_bc40_json,
            "41": ceisa_export.get_ceisa_bc41_json,
            "261": ceisa_export.get_ceisa_bc261_json,
            "262": ceisa_export.get_ceisa_bc262_json,
            "331": ceisa_export.get_ceisa_p3bet_json,
            "511": ceisa_export.get_ceisa_ftz011_json,
            "512": ceisa_export.get_ceisa_ftz012_json,
            "513": ceisa_export.get_ceisa_ftz013_json
        }
        
        export_func = EXPORT_MAP.get(str(bc_type))
        if not export_func:
            return {"status": "error", "message": f"Document type {bc_type} is not supported for automatic sending yet."}

        # Generate payload
        payload = export_func(docname)
        
        if isinstance(payload, dict) and payload.get("status") == "error":
             return payload 
        
        url = f"{BEACUKAI_BASE_URL}/openapi/document?isFinal=false"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        return {
            "status": "success" if response.status_code == 200 else "error",
            "http_code": response.status_code,
            "response": response.json() if response.content else response.text
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send CEISA Document Error")
        return {"status": "error", "message": str(e)}

