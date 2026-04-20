"""
CEISA Authentication & Shared Helpers
=====================================

Shared authentication functions used by all CEISA API modules.
Handles login, token caching, and header construction.
"""

import json
import frappe
import requests


def get_ceisa_settings():
    """Get CEISA Settings singleton document"""
    try:
        return frappe.get_single("CEISA Settings")
    except Exception:
        frappe.throw("CEISA Settings belum dikonfigurasi. Silakan buka CEISA Settings dan isi konfigurasi.")


def get_cached_token():
    """Get cached Bearer token from login"""
    return frappe.cache().hget("beacukai_token", frappe.session.user)


def build_auth_headers(token):
    """Build headers with Bearer token for authenticated API calls"""
    settings = get_ceisa_settings()
    api_key = settings.get_password("api_key") if settings.api_key else None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    if api_key:
        headers["beacukai-api-key"] = api_key

    return headers


def ensure_login():
    """Ensure user is logged in, auto-login with default credentials if needed.

    Returns:
        str: Bearer token

    Raises:
        frappe.ValidationError if login fails or token is missing
    """
    token = get_cached_token()
    if token:
        return token

    # Auto-login with default credentials
    settings = get_ceisa_settings()
    username = settings.default_username
    password = settings.get_password("default_password") if settings.default_password else None

    if not username or not password:
        frappe.throw("Sesi CEISA habis. Silakan Login manual atau lengkapi Default Username/Password di CEISA Settings.")

    result = login_beacukai(username, password)
    
    if result.get("status") == "success":
        new_token = get_cached_token()
        if new_token:
            return new_token
        
        # Succeeded but no token cached (case where API says success but no token in response)
        msg = result.get("note") or "Login berhasil tapi token tidak ditemukan dalam respons CEISA."
        frappe.throw(msg)

    # Login failed
    frappe.throw(f"Auto-login CEISA gagal: {result.get('message')}")


def refresh_token():
    """Refresh the Bearer token using /v1/openapi-auth/user/update-token.

    Called automatically when a 401 (token expired) is received.
    Updates the token cache on success.

    Returns:
        str: New token, or None if refresh failed.
    """
    try:
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        old_token = get_cached_token()

        if not old_token:
            # No token at all — attempt a full re-login
            result = ensure_login()
            return get_cached_token()

        headers = build_auth_headers(old_token)
        url = f"{base_url}/v1/openapi-auth/user/update-token"

        response = requests.post(url, headers=headers)
        data = response.json() if response.content else {}

        # Extract new token from various possible response shapes
        new_token = None
        item = data.get("item")

        if item:
            if isinstance(item, dict):
                new_token = item.get("access_token") or item.get("token") or item.get("accessToken")
            elif isinstance(item, str):
                new_token = item
        
        if not new_token:
            new_token = data.get("access_token") or data.get("token") or data.get("accessToken")
        
        if not new_token and isinstance(data.get("data"), dict):
            new_token = data["data"].get("access_token") or data["data"].get("token") or data["data"].get("accessToken")

        if new_token:
            frappe.cache().hset("beacukai_token", frappe.session.user, new_token)
            frappe.log_error(f"Token refreshed via update-token", "Token Refresh")
            return new_token

        # update-token failed — try full re-login with default credentials
        frappe.log_error(
            f"update-token returned no token (HTTP {response.status_code}): {data}",
            "Token Refresh Warning"
        )
        settings = get_ceisa_settings()
        username = settings.default_username
        password = settings.get_password("default_password") if settings.default_password else None
        if username and password:
            result = login_beacukai(username, password)
            if result.get("status") == "success":
                return get_cached_token()

        return None

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Token Refresh Error")
        return None


@frappe.whitelist()
def login_beacukai(username, password):
    """Login to CEISA 4.0 API and obtain Bearer token.

    Endpoint: POST /v1/openapi-auth/user/login
    """
    try:
        settings = get_ceisa_settings()
        base_url = settings.base_url or "https://apis-gw.beacukai.go.id"
        api_key = settings.get_password("api_key") if settings.api_key else None

        url = f"{base_url}/v1/openapi-auth/user/login"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["beacukai-api-key"] = api_key

        payload = {
            "username": username,
            "password": password,
            "client_id": settings.client_id,
            "client_secret": settings.get_password("client_secret") if settings.client_secret else None
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract token from response (handle various CEISA response formats)
        token = None
        item = data.get("item")

        if item:
            if isinstance(item, dict):
                token = item.get("access_token") or item.get("token") or item.get("accessToken")
            elif isinstance(item, str):
                token = item
        
        if not token:
            token = data.get("access_token") or data.get("token") or data.get("accessToken")
        
        # Check in a 'data' field as some endpoints wrap it there
        if not token and isinstance(data.get("data"), dict):
            token = data["data"].get("access_token") or data["data"].get("token") or data["data"].get("accessToken")

        if token:
            frappe.cache().hset("beacukai_token", frappe.session.user, token)
            masked_token = f"{str(token)[:8]}...{str(token)[-8:]}" if len(str(token)) > 16 else str(token)
            return {"status": "success", "message": f"Login successful. Token: {masked_token}"}

        # Login success but no token returned — log for debugging
        if data.get("status") == "success" or response.status_code == 200:
            frappe.log_error(f"CEISA Login success but no token found in JSON: {json.dumps(data)}", "CEISA Auth Debug")
            return {
                "status": "success",
                "message": data.get("message", "Login successful (No Token)"),
                "note": "Login berhasil tapi token tidak ditemukan dalam respons API.",
                "response": data
            }

        return {"status": "error", "message": "Login failed", "response": data}

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Beacukai Login Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Beacukai Login Error")
        return {"status": "error", "message": str(e)}
