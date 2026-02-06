import frappe

def execute():
    # 1. Update Custom Field definition
    field_name = "CRM Lead-indiamart_message"
    if frappe.db.exists("Custom Field", field_name):
        frappe.db.set_value("Custom Field", field_name, "fieldtype", "Small Text") 
        # Using Small Text as it is the standard 'Textarea'. 'Text' is also valid but Small Text is more common for this.
        # Wait, user complained about one line. Small Text *should* be textarea.
        # Let's use "Text" to be sure it's distinct.
        frappe.db.set_value("Custom Field", field_name, "fieldtype", "Text")
        print(f"Updated {field_name} fieldtype to Text.")
    else:
        print(f"Custom Field {field_name} not found.")

    # 2. Clean up existing data (Replace <br> with \n)
    leads = frappe.get_all("CRM Lead", fields=["name", "indiamart_message"])
    print(f"Checking {len(leads)} leads for HTML cleanup...")
    
    count = 0
    for lead in leads:
        msg = lead.get("indiamart_message")
        if msg and ("<br>" in msg or "<br/>" in msg):
            clean_msg = msg.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            frappe.db.set_value("CRM Lead", lead.name, "indiamart_message", clean_msg)
            count += 1
            
    print(f"Cleaned up HTML tags in {count} leads.")
    frappe.db.commit()

if __name__ == "__main__":
    execute()
