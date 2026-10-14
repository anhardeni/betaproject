import re

def normalize_sap_id(raw_id: str, target_length: int = 10) -> str:
    """
    Mengubah ID mentah menjadi format standar SAP (dengan leading zeroes).
    
    Contoh:
      - '10034' -> '0000010034' (SAP Standard 10-digit)
      - '10002341' -> '000000000010002341' (SAP Material 18-digit jika target_length=18)
    """
    if not raw_id:
        return ""
        
    clean_id = str(raw_id).strip()
    
    # Jika alfanumerik murni (misal: 'CUST-A1'), tidak di-pad dengan nol
    if not clean_id.isdigit():
        return clean_id
        
    return clean_id.zfill(target_length)


def strip_sap_padding(sap_id: str) -> str:
    """
    Menghapus angka nol di awal untuk perbandingan di ERPNext / kek_it_inventory.
    
    Contoh:
      - '0000010034' -> '10034'
    """
    if not sap_id:
        return ""
    clean_id = str(sap_id).strip()
    return clean_id.lstrip("0") if clean_id.isdigit() else clean_id
