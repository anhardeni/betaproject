# Add CEISA Document Detail Staging Table and API Endpoint

We are adding a whitelisted API endpoint `/api/method/singlecore_apps.api.ceisa_api.document.get_document_detail` that calls the CEISA 4.0 document detail API, and a new staging DocType `Ceisa Document Detail` to store the raw nested JSON results in a `raw_json` field with elevated search columns in the background.

## User Review Required

> [!IMPORTANT]
> The new `Ceisa Document Detail` DocType acts as a staging table. In the background, when `sync_to_db` is set to `True`, we will asynchronously save the staging record using `frappe.enqueue`.
> This avoids blocking the live API request, ensuring a highly responsive frontend while background workers safely write to the database.

## Open Questions

There are no remaining open questions as we resolved the design decisions interactively during the `/grill-me` session.

---

## Proposed Changes

### CEISA API Module

#### [MODIFY] [document.py](file:///wsl.localhost/Ubuntu-24.04/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/api/ceisa_api/document.py)
- Import `frappe.enqueue` or define a background job handler to save staging records.
- Implement `@frappe.whitelist() def get_document_detail(jenis_dokumen, nomor_aju, kode_kantor, sync_to_db=False)`.
- Make a GET request to CEISA's `GET /openapi/document/{jenis_dokumen}/{nomor_aju}/{kode_kantor}` using the credentials stored in the `Ceisa Settings` singleton.
- Return a structured response: `{ "status": "success" / "error", "http_code": response.status_code, "data": ... }`.
- If `sync_to_db` is `True`, queue a background worker task using `frappe.enqueue` to create/update the `Ceisa Document Detail` DocType record.

#### [MODIFY] [__init__.py](file:///wsl.localhost/Ubuntu-24.04/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/api/ceisa_api/__init__.py)
- Expose the new `get_document_detail` method.

---

### Doctype: Ceisa Document Detail [NEW]

We will create a new directory `ceisa_document_detail` under the `doctype/` package.

#### [NEW] [__init__.py](file:///wsl.localhost/Ubuntu-24.04/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/singlecore_apps/doctype/ceisa_document_detail/__init__.py)
- Empty init file.

#### [NEW] [ceisa_document_detail.py](file:///wsl.localhost/Ubuntu-24.04/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/singlecore_apps/doctype/ceisa_document_detail/ceisa_document_detail.py)
- Python class controller for `Ceisa Document Detail`.

#### [NEW] [ceisa_document_detail.json](file:///wsl.localhost/Ubuntu-24.04/home/acer25/frappe-bench/apps/singlecore_apps/singlecore_apps/singlecore_apps/doctype/ceisa_document_detail/ceisa_document_detail.json)
- DocType JSON schema containing:
  - Autoname: `field:nomor_aju` (to use the unique Nomor Aju as the document ID).
  - Fields:
    - `nomor_aju` (Data, bold, unique, required)
    - `jenis_dokumen` (Data, required)
    - `kode_kantor` (Data)
    - `nomor_daftar` (Data)
    - `tanggal_daftar` (Date)
    - `raw_json` (Long Text)
    - `status` (Select: Success, Error, Pending)
    - `message` (Small Text)
    - `retrieved_at` (Datetime)

---

## Verification Plan

### Automated Tests
- Create a test file `test_ceisa_document_detail.py` or run a manual test script inside the workspace to execute the endpoint.
- Verify status codes and check if the database records are created and populated properly in background tasks.

### Manual Verification
- We can verify the endpoint response directly from a python bench console run or by executing the whitelisted API through curl or postman.
