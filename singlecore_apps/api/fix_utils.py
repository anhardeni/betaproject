import frappe

def fix_visibility(): # Reuse function name for easy execution
    print("Checking Error Logs (Last 5)...")
    logs = frappe.get_all("Error Log", fields=["method", "error", "creation"], order_by="creation desc", limit=5)
    if logs:
        for log in logs:
            print(f"[{log.creation}] Method: {log.method}")
            print(f"Error: {log.error[:500]}...") # Truncate
            print("-" * 40)
    else:
        print("No Error Logs found.")
