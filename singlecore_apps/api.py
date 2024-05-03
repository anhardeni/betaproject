from os import stat
import frappe
from frappe.query_builder import DocType


SUCCESS = 200
NOT_FOUND = 400


@frappe.whitelist(allow_guest=True)
def get_all_headerg():
    headerg = frappe.db.sql("""SELECT kode_kantor_bongkar AS kodeKantorBongkar, kode_dokumen  FROM `tabHEADER V2` ;""", as_dict=True)

    return headerg

@frappe.whitelist(allow_guest=True)
def get_all_headera1():
    headera1 = frappe.db.sql("""SELECT kode_kantor_bongkar AS kodeKantorBongkar, JSON_ARRAYAGG(kode_dokumen) FROM `tabHEADER V2` ;""", as_dict=True)

    return headera1


@frappe.whitelist(allow_guest=True)
def get_all_headerq():
    #headerq = frappe.qb.Table("tabHEADER")
    headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq = frappe.qb.from_('HEADER').select('name').as_('nomorAju').run(as_dict=True)
    return headerq
    #str(query)
    # SELECT "id","fname","lname","phone" FROM "tabCustomer"

    #query.get_sql()
    # SELECT "id","fname","lname","phone" FROM "tabCustomer"

    #str(query) == query.get_sql()



    #headerq = frappe.qb.DocType('HEADER')
        #filtered_data = (
            #frappe.qb.from_(headerq)
                #.select(headerq.kode_kantor_bongkar, headerq.nomoraju, headerq.name, headerq.referensi_kantor)
                #.where((customer.fname == 'Max') | customer.id.like('RA%'))
                #.where(customer.lname == 'Mustermann')
        #).run(as_dict=True)

    #return headerq

@frappe.whitelist(allow_guest=True)
def get_all_bc20():
    bc20 = frappe.db.sql("""SELECT 
    name AS nomorAju,
    kode_kantor_bongkar AS kodeKantorBongkar, 
    kode_dokumen  
    FROM `tabHEADER V2` ;""", as_dict=True)

    return bc20


@frappe.whitelist(allow_guest=True)
def get_all_bc30():
    bc30 = frappe.db.sql("""SELECT 
    asaldata	AS	asalData	,
    asuransi	AS	asuransi	,
    barang_tidak_berwujud	AS	barang_tidak_berwujud	,
    biaya_pengurang	AS	biaya_pengurang	,
    biaya_tambahan	AS	biaya_tambahan	,
    bruto	AS	bruto	,
    cif	AS	cif	,
    kode_kantor_bongkar AS kodeKantorBongkar, 
    kode_dokumen  
    FROM `tabHEADER V2`
    WHERE `tabHEADER V2`.kode_dokumen = "30"
        AND  `tabHEADER V2`.name = "000030BT000120231002000013"     ;""", as_dict=True)

    return bc30

@frappe.whitelist(allow_guest=True)
def get_all_headerq30():
    #headerq30 = frappe.qb.Table("tabHEADER")
    #headerq30 = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).where('kode_dokumen' == '261').walk(as_dict=True)
    headerq30 = frappe.qb.from_('HEADER V2').select('name' , 'owner', 'nomoraju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq30 = frappe.qb.from_('HEADER V2').select('name').as_('nomorAju').run(as_dict=True)
    return headerq30

@frappe.whitelist(allow_guest=True)
def get_all_headerl1():
    frappe.get_list("HEADER V2")
    #headerq = frappe.qb.from_('HEADER').select('name' , 'owner', 'nomor_aju' , 'kode_dokumen' ).run(as_dict=True)
    #headerq30 = frappe.qb.from_('HEADER V2').select('name').as_('nomorAju').run(as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_all_bc301():
    bc301 = frappe.db.sql("""SELECT JSON_OBJECT(
        asaldata,asalData	
        , Asuransi,	Asuransi
        , kode_kantor ,	kode_Kantor 
    )
    FROM `tabHEADER V2`
         ;""", as_dict=True)

    return bc301

@frappe.whitelist(allow_guest=True)
def get_all_bctest01():
    bctest01 = frappe.db.sql("""select json_object(
        'id',p.id
        ,'desc',p.desc
        ,'child_objects',JSON_EXTRACT(IFNULL((select
        CONCAT('[',GROUP_CONCAT(
        json_object('id',c.id,'parent_id',c.parent_id,'desc',c.desc)
        ),']')   
        from `child_table` c where  c.parent_id = p.id),'[]'),'$')
        ) from `parent_table` p where p.id = 2;""", as_dict=True)

    return bctest01



frappe.whitelist(allow_guest=True)
def authenticate_and_get_token(username, password):
    auth_url = "https://example.com/api/authenticate"
    auth_data = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        token = response.json().get("access_token")
        if token:
            return token
        else:
            raise ValueError("No access token found in response")
    except requests.exceptions.RequestException as e:
        print("Authentication error:", e)
        return None

def get_parent_data():
    parent_data = {}

    # Query to fetch parent data and its related children and grandchildren
    parents = frappe.get_all("Parent", filters={"name": "Parent1"}, fields=["name"])
    for parent in parents:
        parent_name = parent.name
        children = frappe.get_all("Child", filters={"parent": parent_name}, fields=["name"])
        parent_data[parent_name] = {"children": {}}
        for child in children:
            child_name = child.name
            grandchildren = frappe.get_all("Grandchild", filters={"parent": child_name}, fields=["name"])
            parent_data[parent_name]["children"][child_name] = {"grandchildren": []}
            for grandchild in grandchildren:
                parent_data[parent_name]["children"][child_name]["grandchildren"].append(grandchild.name)

    return parent_data


def send_data_to_other_app(data, token):
    url = "https://example.com/api/data"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        print("Data sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error sending data:", e)

# Example usage:
    username = "your_username"
    password = "your_password"

    token = authenticate_and_get_token(username, password)
    if token:
        parent_data = get_parent_data()
        send_data_to_other_app(parent_data, token)


@frappe.whitelist(allow_guest=True)
def get_nested_data():
    # Example: Retrieve data from Frappe doctypes
    #parent_data = frappe.get_doc("HEADER V2", "nomoraju")
    parent_data = frappe.get_doc("HEADER V2", "000023BT000120240110000050")
    #entitas_data = frappe.get_doc("ENTITAS",  "000023BT000120240110000050")
    children_data = frappe.get_list("BARANG V1", filters={"nomoraju": "000023BT000120240110000050"}, fields=['nomoraju', 'seri_barang', 'name'],)
    #grandchildren_data = frappe.get_all("GrandchildDoctype", filters={"parent": "parent_docname"})

    # Format the data into the nested JSON structure with aliases
    nested_data = {
        "data": {
            "asalData": parent_data.asaldata,  # Alias for parent field 1
            "Nomor_aju_dok": parent_data.name,  # Alias for parent field 1
            "Kode_dokumen_dok": parent_data.kode_dokumen,  # Alias for parent field 2
            "CIF": int(parent_data.cif),
            # "entitas": [
            #     {
            #         "kode_entitas": entitas.kode_entitas
            #     }
            #     for entitas in entitas_data
            # ],
            "children": [
                {
                    "Nomor_aju_brg": child.nomoraju,  # Alias for child field 1
                    "kode_brg": child.name,  # Alias for child field 1
                    "Seri_barang_brg": child.seri_barang  # Alias for child field 2
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for child in children_data
            ]
        }
    }

    return nested_data

@frappe.whitelist(allow_guest=True)
def get_nested_data_all():
    # Example: Retrieve data from Frappe doctypes
    #parent_data = frappe.get_doc("HEADER V2", "nomoraju")
    parent_data = frappe.get_doc("HEADER V2", "000023BT000120240110000050")
    entitas_data = frappe.get_list("ENTITAS",  filters={"parent": "000023BT000120240110000050"}, fields=[ 'seri', 'kode_entitas'],)
    #entitas_data = parent_data.as_dict().get('ENTITAS', [])
    #entitas_data = [entitas.as_dict() for entitas in parent_data.get("nomoraju")]
    children_data = frappe.get_list("BARANG V1", filters={"nomoraju": "000023BT000120240110000050"}, fields=['nomoraju', 'seri_barang', 'name'],)
    

    # Format the data into the nested JSON structure with aliases
    nested_data_all = {
        "data": {
            "asalData": parent_data.asaldata,  # Alias for parent field 1
            "Nomor_aju_dok": parent_data.name,  # Alias for parent field 1
            "Kode_dokumen_dok": parent_data.kode_dokumen,  # Alias for parent field 2
            "CIF": int(parent_data.cif),
            "entitas": [
                {
                    "seri_barang": entitas.seri,
                    "kodeEntitas": entitas.kode_entitas,
                }
                for entitas in entitas_data
            ],
            "children": [
                {
                    "Nomor_aju_brg": child.nomoraju,  # Alias for child field 1
                    "kode_brg": child.name,  # Alias for child field 1
                    "Seri_barang_brg": child.seri_barang  # Alias for child field 2
                    #"grandchildren": [
                    #    {
                    #        "grandchild_field1": grandchild.grandchild_field1,  # Alias for grandchild field 1
                    #        "grandchild_field2": grandchild.grandchild_field2  # Alias for grandchild field 2
                    #    }
                    #    for grandchild in grandchildren_data if grandchild.parent == child.name
                    #]
                }
                for child in children_data
            ]
        }
    }

    return nested_data_all






 