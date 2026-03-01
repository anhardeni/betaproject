"""
CEISA Authentication & Shared Helpers
=====================================

Shared authentication functions used by all CEISA API modules.
Handles login, token caching, and header construction.
"""

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
        frappe.ValidationError if login fails
    """
    token = get_cached_token()
    if token:
        return token

    # Auto-login with default credentials
    settings = get_ceisa_settings()
    username = settings.default_username
    password = settings.get_password("default_password") if settings.default_password else None

    if not username or not password:
        frappe.throw("Tidak ada session aktif. Silakan login terlebih dahulu atau isi Default Username/Password di CEISA Settings.")

    result = login_beacukai(username, password)
    if result.get("status") != "success":
        frappe.throw(f"Auto-login gagal: {result.get('message')}")

    return get_cached_token()


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
        if data.get("item") and isinstance(data["item"], dict):
            new_token = data["item"].get("access_token")
        elif data.get("item") and isinstance(data["item"], str):
            new_token = data["item"]
        elif data.get("access_token"):
            new_token = data["access_token"]

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
            "password": password
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract token from response
        token = None
        if data.get("item") and isinstance(data["item"], dict):
            token = data["item"].get("access_token")
        elif data.get("item") and isinstance(data["item"], str):
            token = data["item"]
        elif data.get("access_token"):
            token = data["access_token"]

        if token:
            frappe.cache().hset("beacukai_token", frappe.session.user, token)
            return {"status": "success", "message": "Login successful"}

        # Login success but no token returned
        if data.get("status") == "success":
            return {
                "status": "success",
                "message": data.get("message", "Login successful"),
                "note": "Login berhasil tapi belum ada token.",
                "response": data
            }

        return {"status": "error", "message": "Login failed", "response": data}

    except requests.exceptions.HTTPError as e:
        frappe.log_error(frappe.get_traceback(), "Beacukai Login Error")
        return {"status": "error", "message": f"HTTP Error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Beacukai Login Error")
        return {"status": "error", "message": str(e)}
