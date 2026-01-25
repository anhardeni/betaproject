@frappe.whitelist()
def export_to_country(header_name, country_code):
    doc = frappe.get_doc("HEADER V21", header_name)
    
    if country_code == "US":
        return build_ace_json(doc)
    elif country_code == "EU":
        return build_ics2_json(doc)
    elif country_code == "SG":
        return build_tradenet_json(doc)
    # ... dst
