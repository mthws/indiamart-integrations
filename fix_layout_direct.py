import sys
import os

# Add frappe to path
sys.path.append('/home/lenovo/frappe-bench/apps/frappe')

import frappe

def execute():
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

    # Fields definition
    fields = [
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_product_details_section",
            "fieldtype": "Section Break", # Revert to Section Break for nesting
            "label": "IndiaMART Product Details",
            "insert_after": "mobile_no", # Append after Person section
            "in_list_view": 0,
            "read_only": 1,
            "hidden": 0
        },
        {
            "dt": "CRM Lead",
            "fieldname": "query_id_cf",
            "fieldtype": "Data",
            "label": "IndiaMART Query ID",
            "insert_after": "indiamart_product_details_section",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0,
            "unique": 0 
        },
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_product",
            "fieldtype": "Data",
            "label": "IndiaMART Product",
            "insert_after": "query_id_cf",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        },
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_quantity",
            "fieldtype": "Data",
            "label": "IndiaMART Quantity",
            "insert_after": "indiamart_product",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        },
         {
            "dt": "CRM Lead",
            "fieldname": "indiamart_subject",
            "fieldtype": "Data",
            "label": "IndiaMART Subject",
            "insert_after": "indiamart_quantity",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        },
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_category",
            "fieldtype": "Data",
            "label": "IndiaMART Category",
            "insert_after": "indiamart_subject",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        },
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_message",
            "fieldtype": "Small Text",
            "label": "IndiaMART Message",
            "insert_after": "indiamart_category",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        },
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_city",
            "fieldtype": "Data",
            "label": "IndiaMART City",
            "insert_after": "indiamart_message",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        },
        {
            "dt": "CRM Lead",
            "fieldname": "indiamart_state",
            "fieldtype": "Data",
            "label": "IndiaMART State",
            "insert_after": "indiamart_city",
            "in_list_view": 1,
            "read_only": 1,
            "hidden": 0
        }
    ]

    print("Updating Custom Fields directly...")
    
    for field in fields:
        # Check if exists
        exists = frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]})
        if exists:
            doc = frappe.get_doc("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]})
            doc.update(field)
            doc.save()
            print(f"Updated {field['fieldname']} (Fieldtype: {field['fieldtype']})")
        else:
            doc = frappe.new_doc("Custom Field")
            doc.update(field)
            doc.insert()
            print(f"Created {field['fieldname']}")

    frappe.clear_cache(doctype="CRM Lead")
    frappe.db.commit()
    print("Cache cleared. Layout updated.")

if __name__ == "__main__":
    execute()
