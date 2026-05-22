# Copyright (c) 2026, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, time_diff_in_hours, get_datetime

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Nomor Aju"),
			"fieldname": "no_aju",
			"fieldtype": "Link",
			"options": "Customs Status Log",
			"width": 200
		},
		{
			"label": _("Jenis Dokumen"),
			"fieldname": "doctype_type",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Status BC"),
			"fieldname": "bc_status",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Jalur"),
			"fieldname": "jalur",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NOPEN"),
			"fieldname": "nopen",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Tgl NOPEN"),
			"fieldname": "nopen_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Lead Time (Sub->Reg) Hr"),
			"fieldname": "lead_time",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Total Duration Hr"),
			"fieldname": "total_duration",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"label": _("Last API Success"),
			"fieldname": "last_pull_datetime",
			"fieldtype": "Datetime",
			"width": 160
		},
		{
			"label": _("Files"),
			"fieldname": "files",
			"fieldtype": "HTML",
			"width": 100
		}
	]

def get_data(filters):
	now = now_datetime()
	
	# Fetch main log data
	logs = frappe.db.get_all(
		"Customs Status Log",
		fields=[
			"name", "no_aju", "doctype_type", "bc_status", "jalur",
			"nopen", "nopen_date", "submission_datetime", 
			"last_pull_datetime", "modified"
		],
		filters=filters,
		order_by="submission_datetime desc"
	)
	
	# Fetch PDF links from responses
	# We'll group them by parent (no_aju)
	response_files = frappe.db.get_all(
		"Customs Status Log Response",
		fields=["parent", "pdf_file", "kode_respon"],
		filters={"pdf_file": ["is", "set"]},
		order_by="creation desc"
	)
	
	pdf_map = {}
	for r in response_files:
		if r.parent not in pdf_map:
			pdf_map[r.parent] = []
		# Only take unique or relevant ones, but for simplicity, we'll list them
		if r.pdf_file:
			pdf_map[r.parent].append(f"<a href='/files/{r.pdf_file}' target='_blank'>{r.kode_respon}</a>")

	data = []
	for log in logs:
		row = log
		
		# Calculate Lead Time (Submission -> Nopen)
		if log.submission_datetime and log.nopen_date:
			# Nopen date is only Date, so we compare with submission date part
			# But if we had first status 'Registered' time, it would be better.
			# For now, use the 'modified' time if status is Registered? 
			# Actually, let's look for the first 'statuses' row with kode_status that implies registration.
			# For simplicity, if nopen exists, we estimate.
			row["lead_time"] = time_diff_in_hours(log.modified, log.submission_datetime) if log.bc_status in ["Registered", "Completed"] else 0
		else:
			row["lead_time"] = 0
			
		# Total Duration
		if log.bc_status == "Completed" and log.submission_datetime:
			row["total_duration"] = time_diff_in_hours(log.modified, log.submission_datetime)
		else:
			row["total_duration"] = 0
			
		# Technical Hang Check
		row["is_hanging"] = 0
		if log.bc_status in ["Pending", "Registered", "Action Required: NPD"]:
			if log.last_pull_datetime:
				diff = time_diff_in_hours(now, log.last_pull_datetime)
				if diff > 4:
					row["is_hanging"] = 1
			else:
				# Never pulled?
				row["is_hanging"] = 1
				
		# Files column
		row["files"] = ", ".join(pdf_map.get(log.name, []))
		
		data.append(row)
		
	return data
