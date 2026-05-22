import frappe

def run():
    if not frappe.db.exists('Report', 'Customs Action List'):
        r = frappe.new_doc('Report')
        r.report_name = 'Customs Action List'
        r.ref_doctype = 'Customs Status Log'
        r.report_type = 'Script Report'
        r.is_standard = 'Yes'
        r.module = 'Singlecore Apps'
        r.insert(ignore_permissions=True)
        frappe.db.commit()
        return "Report Created"
    return "Report Exists"
