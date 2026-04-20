import frappe

@frappe.whitelist()
def check_subcontract_codes():
    fields = [f.fieldname for f in frappe.get_meta('DOKUMEN').fields]
    print(f"DOKUMEN fields: {fields}")
