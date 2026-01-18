
code = """

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
    token = get_cached_token()
    if not token:
        return {"status": "error", "message": "Please login to Beacukai first."}
    
    try:
        # Use existing function to get payload
        # Assuming docname passed is the nomor_aju or name
        payload = get_ceisa_bc20_json(docname)
        
        if isinstance(payload, dict) and payload.get("status") == "error":
             return payload # Propagate error from get_ceisa_bc20_json
        
        url = f"{BEACUKAI_BASE_URL}/openapi/document"
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
"""

with open("/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/api.py", "a") as f:
    f.write(code)
