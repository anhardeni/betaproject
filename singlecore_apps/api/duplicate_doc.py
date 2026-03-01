# Copyright (c) 2024, AnharDeni and contributors
# For license information, please see license.txt

"""
duplicate_doc.py
================
Whitelisted server method to duplicate a HEADER V21 document as a brand-new
document (docstatus = 0).

Deep copy hierarchy handled:
  HEADER V21
  ├── Direct child tables (kemasan, pengangkut, dokumen, entitas, …)
  │     → copied automatically by frappe.copy_doc
  └── BARANG V1 records (linked via nomoraju)
        ├── BARANG V1 child tables (barang_tarif, barang_dokumen,
        │     barang_pemilik, barang_spek_khusus, barang_vd)
        │     → copied automatically by frappe.copy_doc on each BARANG V1
        └── BAHAN BAKU records (linked via parent_barang)
              ├── BAHAN BAKU child tables (bahan_baku_dokumen, bahan_tarif)
              │     → copied automatically by frappe.copy_doc on each BAHAN BAKU
              └── nomoraju field updated to new header name

Usage from client:
    frappe.call({
        method: "singlecore_apps.api.duplicate_doc.duplicate_as_new",
        args: { doctype: frm.doctype, name: frm.doc.name },
        ...
    })

Configuration (edit below to customise per-project):
    EXCLUDE_FIELDS       – header fields to blank-out in the new HEADER V21 doc.
    FIELD_MAPPING        – header field → new value overrides after copy.
    COPY_ATTACHMENTS     – if True, File attachments on the header are duplicated.
    COPY_BAHAN_BAKU      – if True, BAHAN BAKU records linked to each BARANG V1
                           are also duplicated (referencing the new BARANG V1).
"""

import frappe
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Fields whose values will be cleared (None) in the new HEADER V21 document.
EXCLUDE_FIELDS = [
    "nomoraju",      # Nomor Aju — unique per submission, must be blank on new doc
    "notifikasi",    # Notifikasi status from Beacukai
]

# Explicit field → value mapping applied AFTER copy_doc to the new HEADER V21.
FIELD_MAPPING = {}

# Copy File attachments linked to the original header (safe; files not deleted).
COPY_ATTACHMENTS = False

# Copy BAHAN BAKU records linked to each BARANG V1.
COPY_BAHAN_BAKU = True


# ---------------------------------------------------------------------------
# Main whitelisted method
# ---------------------------------------------------------------------------

@frappe.whitelist()
def duplicate_as_new(doctype, name):
    """
    Deep-duplicate *name* (a HEADER V21 document) including:
      1. All direct child tables of the header (via frappe.copy_doc).
      2. All BARANG V1 documents linked to the header (each deep-copied with
         their own child tables via frappe.copy_doc, and re-linked to the new
         header).
      3. All BAHAN BAKU documents linked to each BARANG V1 (if COPY_BAHAN_BAKU
         is True), re-linked to the new BARANG V1 and new header.

    Returns:
        dict: {
            "doctype": str,
            "name":    str,   ← new HEADER V21 name
            "summary": str,   ← HTML summary shown in msgprint
        }

    Raises:
        frappe.PermissionError   if the user lacks READ or CREATE permission.
        frappe.DoesNotExistError if *name* does not exist.
        frappe.ValidationError   if arguments are invalid.
    """
    # ------------------------------------------------------------------
    # 1. Input validation
    # ------------------------------------------------------------------
    if not doctype or not isinstance(doctype, str):
        frappe.throw(frappe._("Parameter 'doctype' is required and must be a string."),
                     frappe.ValidationError)
    if not name or not isinstance(name, str):
        frappe.throw(frappe._("Parameter 'name' is required and must be a string."),
                     frappe.ValidationError)

    doctype = doctype.strip()
    name    = name.strip()

    # ------------------------------------------------------------------
    # 2. Permission checks
    # ------------------------------------------------------------------
    if not frappe.has_permission(doctype, ptype="read", doc=name):
        frappe.throw(
            frappe._("You do not have READ permission on {0} {1}.").format(doctype, name),
            frappe.PermissionError,
        )
    if not frappe.has_permission(doctype, ptype="create"):
        frappe.throw(
            frappe._("You do not have CREATE permission on DocType {0}.").format(doctype),
            frappe.PermissionError,
        )

    # ------------------------------------------------------------------
    # 3. Load original HEADER V21
    # ------------------------------------------------------------------
    doc = frappe.get_doc(doctype, name)

    # ------------------------------------------------------------------
    # 4. Discover direct child tables via meta (for logging/summary only;
    #    frappe.copy_doc handles copying them automatically)
    # ------------------------------------------------------------------
    meta = frappe.get_meta(doctype)
    header_child_tables = meta.get_table_fields()

    header_child_info = []
    for tf in header_child_tables:
        child_rows = getattr(doc, tf.fieldname, []) or []
        header_child_info.append({
            "fieldname":     tf.fieldname,
            "child_doctype": tf.options,
            "row_count":     len(child_rows),
        })
        logger.info(
            "[duplicate_as_new] Header child table '%s' (%s): %d rows",
            tf.fieldname, tf.options, len(child_rows),
        )

    # ------------------------------------------------------------------
    # 5. Deep copy the HEADER V21 (includes all direct child table rows)
    # ------------------------------------------------------------------
    new_header = frappe.copy_doc(doc)
    new_header.docstatus = 0

    # FIX: kode_dokumen4digit is a fetch_if_empty/read_only field.
    # Documents imported via import_ceisa_excel have this field NULL in
    # the DB (fetch was never triggered), so copy_doc also copies NULL.
    # We MUST fetch it explicitly from Referensi Dokumen before insert(),
    # otherwise the autoname rule:
    #   format:{00}{kode_dokumen4digit}{900001}{YYYY}{MM}{DD}{######}
    # produces a 22-char name (missing 4 chars) instead of 26 chars.
    kode_dok = new_header.kode_dokumen
    if kode_dok:
        kode_4digit = frappe.db.get_value(
            "Referensi Dokumen", kode_dok, "nama_dok4digit"
        )
        if kode_4digit:
            new_header.kode_dokumen4digit = kode_4digit
            logger.info(
                "[duplicate_as_new] kode_dokumen4digit set to '%s' from Referensi Dokumen[%s]",
                kode_4digit, kode_dok,
            )
        else:
            # Fallback: zero-pad kode_dokumen to 4 digits
            new_header.kode_dokumen4digit = str(kode_dok).zfill(4)
            logger.warning(
                "[duplicate_as_new] nama_dok4digit not found for kode_dokumen='%s', "
                "using zero-padded fallback '%s'",
                kode_dok, new_header.kode_dokumen4digit,
            )

    # -- Post-copy cleanup on the header --
    for fieldname in EXCLUDE_FIELDS:
        if hasattr(new_header, fieldname):
            setattr(new_header, fieldname, None)

    for fieldname, new_value in FIELD_MAPPING.items():
        if hasattr(new_header, fieldname):
            setattr(new_header, fieldname, new_value)

    # Optional: copy file attachments for the header
    if COPY_ATTACHMENTS:
        _copy_attachments(doctype, name, new_header)

    # Bypass link validation (original doc may have been imported without
    # link validation — e.g. kode_tujuan_pengiriman="1" not in Referensi)
    new_header.flags.ignore_links = True
    new_header.insert(ignore_permissions=False)

    # Sync nomoraju = name after insert so the display field matches the
    # newly auto-generated document name (they should always be identical
    # for HEADER V21 records created inside this system).
    if new_header.nomoraju != new_header.name:
        frappe.db.set_value("HEADER V21", new_header.name, "nomoraju", new_header.name)
        new_header.nomoraju = new_header.name

    logger.info(
        "[duplicate_as_new] HEADER V21 %s → new: %s (nomoraju=%s)",
        name, new_header.name, new_header.nomoraju,
    )

    # ------------------------------------------------------------------
    # 6. Fetch all BARANG V1 linked to the original header via `nomoraju`
    # ------------------------------------------------------------------
    barang_list = frappe.get_all(
        "BARANG V1",
        filters={"nomoraju": name},
        fields=["name"],
        order_by="seri_barang asc",
    )

    barang_summary = []

    for barang_entry in barang_list:
        old_barang_name = barang_entry["name"]
        barang_doc = frappe.get_doc("BARANG V1", old_barang_name)

        # Collect BARANG V1 child table info for logging
        barang_meta = frappe.get_meta("BARANG V1")
        barang_child_infos = []
        for tf in barang_meta.get_table_fields():
            rows = getattr(barang_doc, tf.fieldname, []) or []
            barang_child_infos.append({
                "fieldname": tf.fieldname,
                "row_count": len(rows),
            })

        # Deep copy BARANG V1 (copies barang_tarif, barang_dokumen,
        # barang_pemilik, barang_spek_khusus, barang_vd automatically)
        new_barang = frappe.copy_doc(barang_doc)
        new_barang.docstatus = 0

        # Re-link the new BARANG V1 to the new HEADER V21
        new_barang.nomoraju = new_header.name

        # Insert — bypass link validation for same reason as header
        new_barang.flags.ignore_links = True
        new_barang.insert(ignore_permissions=True)

        logger.info(
            "[duplicate_as_new] BARANG V1 %s → new: %s  (linked to header %s)",
            old_barang_name, new_barang.name, new_header.name,
        )

        # Build per-barang summary
        child_detail = ", ".join(
            f"{c['fieldname']}: {c['row_count']} rows"
            for c in barang_child_infos
        )
        barang_summary.append({
            "old_name":  old_barang_name,
            "new_name":  new_barang.name,
            "seri":      barang_doc.seri_barang,
            "children":  barang_child_infos,
        })

        # --------------------------------------------------------------
        # 7. Copy BAHAN BAKU linked to this BARANG V1 (if enabled)
        # --------------------------------------------------------------
        if COPY_BAHAN_BAKU:
            bahan_baku_list = frappe.get_all(
                "BAHAN BAKU",
                filters={"parent_barang": old_barang_name},
                fields=["name"],
                order_by="seri_bahan_baku asc",
            )

            for bb_entry in bahan_baku_list:
                bb_doc = frappe.get_doc("BAHAN BAKU", bb_entry["name"])

                # Deep copy BAHAN BAKU (copies bahan_baku_dokumen,
                # bahan_tarif automatically)
                new_bb = frappe.copy_doc(bb_doc)
                new_bb.docstatus = 0

                # Re-link to the new BARANG V1 and new HEADER V21
                new_bb.parent_barang = new_barang.name
                new_bb.nomoraju      = new_header.name

                new_bb.flags.ignore_links = True
                new_bb.insert(ignore_permissions=True)

                logger.info(
                    "[duplicate_as_new] BAHAN BAKU %s → new: %s  (barang: %s)",
                    bb_entry["name"], new_bb.name, new_barang.name,
                )

    # ------------------------------------------------------------------
    # 8. Build HTML summary for the client msgprint
    # ------------------------------------------------------------------
    summary_lines = [
        f"<b>Original:</b> {name}",
        f"<b>New document:</b> {new_header.name}",
        "",
        "<b>Header child tables duplicated:</b>",
    ]
    for c in header_child_info:
        summary_lines.append(
            f"&nbsp;&nbsp;• {c['fieldname']} ({c['child_doctype']}): "
            f"<b>{c['row_count']}</b> rows"
        )

    summary_lines.append("")
    summary_lines.append(
        f"<b>BARANG V1 duplicated:</b> {len(barang_summary)} record(s)"
    )
    for bs in barang_summary:
        child_detail = " | ".join(
            f"{c['fieldname']}: {c['row_count']}"
            for c in bs["children"] if c["row_count"] > 0
        )
        summary_lines.append(
            f"&nbsp;&nbsp;• Seri {bs['seri']} → {bs['new_name']}"
            + (f"  ({child_detail})" if child_detail else "")
        )

    return {
        "doctype": new_header.doctype,
        "name":    new_header.name,
        "summary": "<br>".join(summary_lines),
    }


# ---------------------------------------------------------------------------
# Helper — copy attachments (safe, non-destructive)
# ---------------------------------------------------------------------------

def _copy_attachments(source_doctype, source_name, new_doc):
    """
    Duplicate File documents linked to *source_name* and attach them to
    *new_doc*.  The original physical files are NOT moved or deleted.
    """
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": source_doctype,
            "attached_to_name":    source_name,
        },
        fields=["file_name", "file_url", "is_private"],
    )

    for f in files:
        try:
            file_doc = frappe.get_doc({
                "doctype":             "File",
                "file_name":           f.file_name,
                "file_url":            f.file_url,
                "is_private":          f.is_private,
                "attached_to_doctype": new_doc.doctype,
                "attached_to_name":    new_doc.name,
            })
            file_doc.insert(ignore_permissions=True)
        except Exception as exc:
            logger.warning(
                "[duplicate_as_new] Could not copy attachment '%s': %s",
                f.file_name, exc,
            )
