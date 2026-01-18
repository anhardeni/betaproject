# Implementation Plan - Beacukai API Integration

This plan outlines the "Multi-Agent" approach to integrating Singlecore Apps with the Beacukai API.

## User Review Required
- **Credentials Storage**: We will store the JWT token in the server-side cache (Redis) linked to the active user session. We will NOT store the username/password in the database for security.
- **API URLs**: We will hardcode the URLs for now as requested, but they can be moved to a Settings DocType later.

## Proposed Changes

### Agent 2: API & JWT (Backend)
#### [NEW] [api.py](file:///home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/api.py)
- `login_beacukai(username, password)`: Authenticates with `/nle-oauth/v1/user/login` and caches the token.
- `get_cached_token()`: Helper to retrieve the token.

### Agent 4: Integration Logic (Backend)
#### [MODIFY] [api.py](file:///home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/api.py)
- `send_ceisa_document(doctype, docname)`: Constructs the JSON payload from `HEADER V21` and sends it to `/openapi/document`.
- `check_ceisa_status(nomor_aju)`: Queries `/openapi/status/:nomorAju`.

### Agent 1: UI/UX (Frontend)
#### [MODIFY] [header_v21.js](file:///home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/singlecore_apps/doctype/header_v21/header_v21.js)
- Add "Beacukai" Group Button.
- **Login**: Opens a dialog for credentials.
- **Send**: Triggers document submission.
- **Status**: Triggers status check and displays result.

## Verification Plan

### Agent 3: Testing
- **Manual Verification**:
    1.  Open `HEADER V21`.
    2.  Click "Beacukai" -> "Login". Enter dummy/real credentials. Verify success message.
    3.  Click "Send". Verify API call (check Network tab or server logs).
    4.  Click "Status". Verify status display.
