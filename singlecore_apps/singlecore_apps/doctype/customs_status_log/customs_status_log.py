import frappe
import json
from frappe.model.document import Document
from singlecore_apps.api.ceisa_api.status import get_status_by_nomor_aju

class CustomsStatusLog(Document):
    def autoname(self):
        self.name = self.nomor_aju

@frappe.whitelist()
def fetch_status_api(nomor_aju):
    # Using existing status API module
    result = get_status_by_nomor_aju(nomor_aju)
    
    if result.get("status") != "success":
        return result
        
    data = result.get("data", {})
    
    # Check if doc exists to update or create new
    if frappe.db.exists("Customs Status Log", nomor_aju):
        doc = frappe.get_doc("Customs Status Log", nomor_aju)
    else:
        doc = frappe.new_doc("Customs Status Log")
        doc.nomor_aju = nomor_aju
        doc.name = nomor_aju # Required for attached_to_name
        
    doc.npwp = data.get('npwpPemberitahu')
    doc.fetched_at = frappe.utils.now()
    
    # Update Status History
    doc.set('status_history', [])
    for item in data.get('dataStatus', []):
        doc.append('status_history', {
            'kode_status': item.get('kodeStatus'),
            'uraian': item.get('uraian'),
            'waktu_rekam': item.get('waktuRekam'),
            'status_aju': item.get('statusAju'),
            'nomor_daftar': item.get('nomorDaftar'),
            'tanggal_daftar': item.get('tanggalDaftar'),
            'keterangan': item.get('keterangan')
        })
    
    # Update Respon History
    doc.set('respon_history', [])
    for item in data.get('dataRespon', []):
        pdf_url = ""
        base64_data = item.get('Pdf')
        
        if base64_data:
            try:
                # Create file in Frappe
                file_name = f"Respon_{nomor_aju}_{item.get('kodeRespon')}_{item.get('nomorRespon')}.pdf"
                _file = frappe.get_doc({
                    "doctype": "File",
                    "file_name": file_name,
                    "attached_to_doctype": "Customs Status Log",
                    "attached_to_name": doc.name,
                    "content": base64_data,
                    "decode": True
                })
                _file.insert(ignore_permissions=True)
                pdf_url = _file.file_url
            except Exception as fe:
                frappe.log_error(f"PDF Conversion Error: {str(fe)}", "Customs Status Log")

        doc.append('respon_history', {
            'kode_respon': item.get('kodeRespon'),
            'nomor_daftar': item.get('nomorDaftar'),
            'tanggal_daftar': item.get('tanggalDaftar'),
            'nomor_respon': item.get('nomorRespon'),
            'tanggal_respon': item.get('tanggalRespon'),
            'waktu_respon': item.get('waktuRespon'),
            'keterangan': item.get('keterangan'),
            'pesan_json': json.dumps(item.get('pesan', [])),
            'pdf_base64': pdf_url # Stores the URL to the actual PDF file
        })
    
    if doc.status_history:
        doc.last_status = doc.status_history[-1].kode_status
        
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return doc.as_dict()

# Method for scheduler
def update_all_active_status():
    """
    Scheduler function to update status for all documents 
    that are not in final state (optional logic).
    """
    # Example: fetch status for logs updated in the last 24 hours
    logs = frappe.get_all("Customs Status Log", fields=["nomor_aju"])
    for log in logs:
        try:
            fetch_status_api(log.nomor_aju)
        except Exception:
            pass
