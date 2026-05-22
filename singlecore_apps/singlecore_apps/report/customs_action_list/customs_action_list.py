import frappe
from frappe.utils import now_datetime, time_diff_in_hours

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "no_aju", "label": "Nomor AJU", "fieldtype": "Link", "options": "HEADER V21", "width": 200},
        {"fieldname": "bc_status", "label": "Status", "fieldtype": "Data", "width": 180},
        {"fieldname": "jalur", "label": "Lane", "fieldtype": "Data", "width": 100},
        {"fieldname": "npd_time", "label": "Action Time", "fieldtype": "Datetime", "width": 160},
        {"fieldname": "deadline", "label": "Risk / Deadline", "fieldtype": "Data", "width": 150},
        {"fieldname": "email_status", "label": "Email Status", "fieldtype": "Data", "width": 120},
        {"fieldname": "actions", "label": "Quick Actions", "fieldtype": "Data", "width": 180}
    ]

def get_data(filters):
    # Fetch logs from the 31-day monitoring window that are not Completed
    query = """
        SELECT 
            name, 
            linked_document_name as no_aju, 
            bc_status, 
            jalur
        FROM `tabCustoms Status Log`
        WHERE bc_status != 'Completed' AND creation >= DATE_SUB(NOW(), INTERVAL 31 DAY)
    """
    if filters and filters.get('jalur'):
        query += f" AND jalur = '{filters.get('jalur')}'"
        
    logs = frappe.db.sql(query, as_dict=True)

    res = []
    now = now_datetime()
    
    for log in logs:
        # Get the latest response to check time and email status
        latest_res = frappe.db.sql("""
            SELECT name, waktu_respon, is_email_sent, kode_respon
            FROM `tabCustoms Status Log Response`
            WHERE parent = %s
            ORDER BY waktu_respon DESC LIMIT 1
        """, (log.name,), as_dict=True)

        action_time = None
        email_sent = 0
        response_name = None
        
        if latest_res:
            email_sent = latest_res[0].is_email_sent
            action_time = latest_res[0].waktu_respon
            response_name = latest_res[0].name
                
        deadline = "-"
        risk_score = 0
        
        if log.bc_status == 'Action Required: NPD' and action_time:
            hours_passed = time_diff_in_hours(now, action_time)
            remaining = 24 - hours_passed
            
            if remaining < 0:
                deadline = "🔴 OVERDUE"
                risk_score = 100
            elif remaining <= 4:
                deadline = f"🔴 {int(remaining)}h Remaining"
                risk_score = 80
            elif remaining <= 12:
                deadline = f"🟠 {int(remaining)}h Remaining"
                risk_score = 50
            else:
                deadline = f"🟡 {int(remaining)}h Remaining"
                risk_score = 20
                
            # Increase risk score if Merah/Kuning
            if log.jalur in ["Merah", "Kuning"]:
                risk_score += 10

        email_display = "✅ Sent" if email_sent else "⏳ Pending"

        res.append({
            "no_aju": log.no_aju,
            "bc_status": log.bc_status,
            "jalur": log.jalur or "N/A",
            "npd_time": action_time,
            "deadline": deadline,
            "email_status": email_display,
            "response_name": response_name,
            "log_name": log.name,
            "risk_score": risk_score # Hidden field for sorting
        })
        
    # Sort by Risk Score (Highest first)
    res = sorted(res, key=lambda k: k['risk_score'], reverse=True)
    return res
