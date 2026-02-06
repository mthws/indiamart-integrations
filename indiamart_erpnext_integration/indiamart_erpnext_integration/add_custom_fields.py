import sys
import os

# Add frappe to path
sys.path.append('/home/lenovo/frappe-bench/apps/frappe')

import frappe

def create_custom_fields():
    # Initialize frappe
    bench_path = '/home/lenovo/frappe-bench'
    os.chdir(bench_path)
    
    # Monkeypatch logger to force console output
    import logging
    def get_console_logger(module=None, with_more_info=False):
        logger = logging.getLogger(module)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
             handler = logging.StreamHandler()
             logger.addHandler(handler)
        return logger

    frappe.logger = get_console_logger
        
    frappe.init(site='indiamart', sites_path=os.path.join(bench_path, 'sites'))
    frappe.connect()

    doctype = "CRM Lead"
    
    if not frappe.db.exists("DocType", doctype):
        print(f"Error: DocType '{doctype}' not found. Please check if CRM app is installed or if you meant 'Lead'.")
        return

    custom_fields = {
        doctype: [
            {
                "fieldname": "indiamart_details_section",
                "label": "IndiaMART Details",
                "fieldtype": "Section Break",
                "insert_after": "mobile_no", # Placing after Mobile/Person section
                "in_list_view": 0,
                "read_only": 1
            },
            {
                "fieldname": "indiamart_product",
                "label": "IndiaMART Product",
                "fieldtype": "Data",
                "insert_after": "indiamart_details_section",
                "in_list_view": 1,
                "read_only": 1
            },
            {
                "fieldname": "indiamart_subject",
                "label": "IndiaMART Subject",
                "fieldtype": "Data",
                "insert_after": "indiamart_product",
                "in_list_view": 1,
                "read_only": 1
            },
             {
                "fieldname": "indiamart_category",
                "label": "IndiaMART Category",
                "fieldtype": "Data",
                "insert_after": "indiamart_subject",
                "in_list_view": 1,
                "read_only": 1
            },
            {
                "fieldname": "indiamart_quantity",
                "label": "IndiaMART Quantity",
                "fieldtype": "Data",
                "insert_after": "indiamart_category",
                "in_list_view": 1,
                "read_only": 1
            },
            {
                "fieldname": "indiamart_city",
                "label": "IndiaMART City",
                "fieldtype": "Data",
                "insert_after": "indiamart_quantity",
                "in_list_view": 1,
                "read_only": 1
            },
            {
                "fieldname": "indiamart_state",
                "label": "IndiaMART State",
                "fieldtype": "Data",
                "insert_after": "indiamart_city",
                "in_list_view": 1,
                "read_only": 1
            },
            {
                "fieldname": "indiamart_message",
                "label": "IndiaMART Message",
                "fieldtype": "Small Text",
                "insert_after": "indiamart_state",
                "in_list_view": 1,
                "read_only": 1
            }
        ]
    }

    print(f"Checking/Creating fields for {doctype}...")
    for dt, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": field["fieldname"]}):
                print(f"Creating custom field {field['fieldname']}...")
                cf = frappe.new_doc("Custom Field")
                cf.dt = dt
                cf.update(field)
                cf.insert()
            else:
                print(f"Field {field['fieldname']} already exists.")

    frappe.db.commit()
    frappe.clear_cache(doctype=doctype)
    print("Cleared DocType cache.")

    # Verification
    print("\n--- Verification ---")
    missing = []
    for field in custom_fields[doctype]:
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
             print(f"[OK] {field['fieldname']} exists.")
        else:
             print(f"[FAIL] {field['fieldname']} MISSING!")
             missing.append(field['fieldname'])
    
    if not missing:
        print("\nSUCCESS: All fields created successfully for CRM Lead.")
    else:
        print(f"\nFAILURE: Missing fields: {missing}")

if __name__ == "__main__":
    create_custom_fields()
