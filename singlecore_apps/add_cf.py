import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    create_custom_field('Customs Status Log Response', dict(fieldname='is_email_sent', label='Email Sent', fieldtype='Check', default='0', insert_after='waktu_respon'))
    frappe.db.commit()
    return "Done"
