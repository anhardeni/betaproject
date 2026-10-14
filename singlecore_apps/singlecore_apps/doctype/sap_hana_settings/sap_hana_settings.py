import frappe
from frappe.model.document import Document
from singlecore_apps.utils.sap_hana_connector import SapHanaConnector

class SAPHANASettings(Document):
    pass

@frappe.whitelist()
def test_connection():
    """
    Method untuk menguji koneksi Pull API (OData / REST) ke SAP langsung dari tombol UI Settings.
    """
    try:
        connector = SapHanaConnector()
        return connector.test_api_connection()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error saat menguji koneksi Pull SAP: {str(e)}"
        }
