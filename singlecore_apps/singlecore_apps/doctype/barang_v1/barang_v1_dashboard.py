from frappe import _

def get_data():
    return {
        "fieldname": "parent_barang",
        "transactions": [
            {
                "label": _("Related"),
                "items": ["BAHAN BAKU"]
            }
        ]
    }
