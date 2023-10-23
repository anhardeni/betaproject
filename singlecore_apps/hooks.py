from . import __version__ as app_version

app_name = "singlecore_apps"
app_title = "Singlecore Apps"
app_publisher = "AnharDeni"
app_description = "Single Interface To Ceisa40 dan perijinan"
app_email = "anhardeni@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/singlecore_apps/css/singlecore_apps.css"
# app_include_js = "/assets/singlecore_apps/js/singlecore_apps.js"

# include js, css files in header of web template
# web_include_css = "/assets/singlecore_apps/css/singlecore_apps.css"
# web_include_js = "/assets/singlecore_apps/js/singlecore_apps.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "singlecore_apps/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "singlecore_apps.utils.jinja_methods",
#	"filters": "singlecore_apps.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "singlecore_apps.install.before_install"
# after_install = "singlecore_apps.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "singlecore_apps.uninstall.before_uninstall"
# after_uninstall = "singlecore_apps.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "singlecore_apps.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"singlecore_apps.tasks.all"
#	],
#	"daily": [
#		"singlecore_apps.tasks.daily"
#	],
#	"hourly": [
#		"singlecore_apps.tasks.hourly"
#	],
#	"weekly": [
#		"singlecore_apps.tasks.weekly"
#	],
#	"monthly": [
#		"singlecore_apps.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "singlecore_apps.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "singlecore_apps.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "singlecore_apps.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["singlecore_apps.utils.before_request"]
# after_request = ["singlecore_apps.utils.after_request"]

# Job Events
# ----------
# before_job = ["singlecore_apps.utils.before_job"]
# after_job = ["singlecore_apps.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"singlecore_apps.auth.validate"
# ]

fixtures = [

        #"Referensi Gudang",
        #"Referensi Ijin",
        "Referensi Incoterm",
        "Referensi Jenis API",
        "Referensi Jenis Ekspor",
        "Referensi Jenis Identitas",
       # "Referensi Jenis Impor",
         "Referensi Jenis Jaminan",
        "Referensi Jenis Kemasan",
        "Referensi Jenis Kontainer",
        "Referensi Layanan Fix",
        #"Referensi Jenis Pib",
        "Referensi Jenis Pungutan",
        "Referensi Jenis TPB",
        "Referensi Jenis Tarif",
        "Referensi Jenis Transaksi Perdagangan",
        "Referensi Jenis VD",
        "Referensi Kantor",
        #"Referensi Kapal",
        "Referensi Kategori Barang",
        "Referensi Kategori Ekspor",
        #"Referensi Kategori Keluar FTZ ",
        "Referensi Komoditi Cukai ",
        "Referensi Kondisi Barang ",
        #"Referensi Layanan Fix ",
        "Referensi Lokasi Bayar ",
        "Referensi Negara ",
        "Referensi Pelabuhan Dalam Negeri ",
        "Referensi Pelabuhan Luar Negeri ",
        "Referensi Putusan Petugas ",
        "Referensi Respon ",
        "Referensi Respon_copy1 ",
        "Referensi Satuan Barang ",
        "Referensi Satuan Barang_copy1 ",
        "Referensi Spesifikasi Khusus ",
        "Referensi Status ",
        "Referensi Status Pengusaha ",
        "Referensi Status_copy1 ",
        "Referensi Tipe Kontainer ",
        "Referensi Tujuan Pemasukan ",
        "Referensi Tujuan Pengeluaran ",
        "Referensi Tujuan Pengiriman ",
        "Referensi Tutup Pu ",
        "Referensi Ukuran Kontainer ",
        "Referensi Valuta "   
           
    
]

