frappe.query_reports["Customs Action List"] = {
	"filters": [
		{
			"fieldname": "jalur",
			"label": __("Lane"),
			"fieldtype": "Select",
			"options": "\nHijau\nKuning\nMerah",
			"default": ""
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "deadline" && data && data.deadline) {
			if (data.deadline.includes("OVERDUE") || data.deadline.includes("🔴")) {
				value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
			} else if (data.deadline.includes("🟠")) {
				value = "<span style='color:darkorange; font-weight:bold'>" + value + "</span>";
			} else if (data.deadline.includes("🟡")) {
				value = "<span style='color:#b8860b; font-weight:bold'>" + value + "</span>";
			}
		}

		if (column.fieldname == "jalur" && data && data.jalur) {
			if (data.jalur == "Merah") {
				value = "<span class='indicator-right red'>" + value + "</span>";
			} else if (data.jalur == "Kuning") {
				value = "<span class='indicator-right orange'>" + value + "</span>";
			} else if (data.jalur == "Hijau") {
				value = "<span class='indicator-right green'>" + value + "</span>";
			}
		}

		if (column.fieldname == "email_status" && data && data.email_status) {
			if (data.email_status.includes("✅")) {
				value = "<span style='color:green'>" + value + "</span>";
			} else {
				value = "<span style='color:grey'>" + value + "</span>";
			}
		}

		if (column.fieldname == "actions" && data) {
			let buttons = `
				<button class="btn btn-xs btn-default" onclick="frappe.query_reports['Customs Action List'].manual_poll('${data.log_name}')">
					<i class="fa fa-refresh"></i> Check
				</button>
			`;
			if (data.response_name && !data.email_status.includes("✅")) {
				buttons += `
					<button class="btn btn-xs btn-primary" style="margin-left:5px" onclick="frappe.query_reports['Customs Action List'].resend_email('${data.response_name}')">
						<i class="fa fa-envelope"></i> Resend
					</button>
				`;
			}
			return buttons;
		}

		return value;
	},
	"manual_poll": function(log_name) {
		frappe.call({
			method: "singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log.manual_poll_status",
			args: { log_name: log_name },
			callback: function(r) {
				if(!r.exc) {
					frappe.show_alert({message: __("Status check triggered"), indicator: 'green'});
					cur_report.refresh();
				}
			}
		});
	},
	"resend_email": function(row_name) {
		frappe.call({
			method: "singlecore_apps.singlecore_apps.doctype.customs_status_log.customs_status_log.resend_notification",
			args: { row_name: row_name },
			callback: function(r) {
				if(!r.exc) {
					frappe.show_alert({message: __("Email resend queued"), indicator: 'green'});
					cur_report.refresh();
				}
			}
		});
	}
};
