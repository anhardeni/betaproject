import frappe

def execute():
    try:
        workspaces = frappe.get_all("Workspace")
        updated_workspaces = []
        
        for w in workspaces:
            doc = frappe.get_doc("Workspace", w.name)
            updated = False
            for shortcut in doc.get("shortcuts", []):
                # If stats_filter is '[]' or literally empty JSON array
                if shortcut.stats_filter == '[]':
                    # Only clear it if the target is a Single DocType to be safe,
                    # or just clear it for CEISA Settings specifically.
                    if shortcut.link_to == "CEISA Settings":
                        shortcut.stats_filter = None
                        shortcut.format = None  # Also clear format if needed
                        updated = True
                        print(f"Fixed CEISA Settings in {w.name}")
            
            if updated:
                doc.flags.ignore_permissions = True
                doc.save(ignore_permissions=True)
                updated_workspaces.append(w.name)
                
        if updated_workspaces:
            frappe.db.commit()
            print("Successfully updated Workspaces:", updated_workspaces)
        else:
            print("No workspaces needed updating.")
            
    except Exception as e:
        frappe.db.rollback()
        print("Error:", str(e))
