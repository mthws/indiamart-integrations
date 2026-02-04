# Indiamart Frappe CRM Integration

This app integrates [IndiaMART CRM API (Version 2)](https://help.indiamart.com/knowledge-base/lms-crm-integration-v2/) with [Frappe CRM](https://frappe.io/crm).

## 🚀 Migration to Frappe CRM
This app has been migrated from ERPNext core to the standalone Frappe CRM app. It now uses `CRM Lead` and `CRM Deal` doctypes instead of the old ERPNext `Lead`.

### ✅ Implementation Checklist
- [x] **Target App**: Changed integration target from ERPNext core to **Frappe CRM**.
- [x] **Primary Doctype**: Now creates **CRM Lead** records.
- [x] **Inquiry Mapping**:
    - `UNIQUE_QUERY_ID` → `query_id_cf` (Custom Field)
    - `SENDER_EMAIL` → `email` (Changed from `email_id`)
    - `SENDER_COMPANY` → `organization` (Changed from `company_name`)
- [x] **Repeat Inquiries**: 
    - Automatically detects repeat leads via Mobile/Email.
    - Creates a **CRM Deal** for repeat inquiries from Qualified/Converted leads.
- [x] **Detail Storage**: 
    - Uses **FCRM Note** to store rich HTML details of the inquiry (Product, Category, Message).
    - Stores address information as a separate Note for better visibility.
- [x] **Immediate Processing**:
    - Modified to process leads **instantly** upon insertion.
    - No longer dependent on background workers (bypasses "Queued" status delay).
- [x] **Settings UI**:
    - Updated to link with `CRM Lead Source` and `CRM Deal Status`.
- [x] **Dashboard Integration**:
    - Custom JS to show Indiamart links directly on the **CRM Lead** dashboard.

## Features
- Pulls leads from IndiaMART every 6 minutes.
- Handles Duplicates/Repeat Leads intelligently.
- Maintains Integration Logs for troubleshooting.
- Allows manual lead pull for specific date ranges.

## Setup
1. Get IndiaMART CRM API Key from the [IndiaMART Seller Panel](https://seller.indiamart.com/leadmanager/crmapi).
2. Configure **Indiamart Settings** in Frappe CRM.
3. Map your "Query Types" to `CRM Lead Source`.

Developed by [GreyCube Technologies](https://greycube.in/)
