# Indiamart Integration Migration to Standalone CRM App

## Executive Summary

This document outlines the architecture and implementation plan for migrating the Indiamart ERPNext Integration app from using ERPNext core Lead doctype to the standalone Frappe CRM app's CRM Lead doctype.

---

## 1. Goal

**Primary Objective:** Modify the Indiamart ERPNext Integration app to save leads from Indiamart API to the standalone CRM app's `CRM Lead` doctype and related records, instead of ERPNext's core `Lead` doctype.

**Key Requirements:**
- Maintain all existing functionality (API polling, duplicate detection, lead mapping)
- Preserve integration logs and error handling
- Support both new lead creation and repeat lead handling
- Ensure seamless transition with minimal data loss

---

## 2. Current Architecture Analysis

### 2.1 Indiamart Integration App Structure

**Core Components:**
- **Controller:** `indiamart_erpnext_controller.py` - Main business logic
- **Settings Doctype:** `Indiamart Settings` - Configuration management
- **Lead Tracking:** `Indiamart Lead` - Tracks processed leads
- **Scheduler:** Runs every 6 minutes via cron job
- **Custom Fields:** `Lead-query_id_cf` (stores Indiamart Query ID)

**Current Lead Creation Flow:**
```
1. API Call (every 6 mins) → Fetch leads from Indiamart
2. Create Integration Request → Log API response
3. Create Indiamart Lead records → Queue for processing
4. Process each lead:
   a. Check duplicate by query_id_cf
   b. Check duplicate by mobile_no
   c. Check duplicate by email_id
   d. Create new Lead OR update existing Lead
   e. Create Address record (linked to Lead)
   f. For repeat leads: Update notes OR create Opportunity
```

### 2.2 ERPNext Lead Doctype (Current Target)

**Key Fields Used:**
- `lead_name` - Full name
- `first_name` - Person's first name
- `email_id` - Email address
- `mobile_no` - Mobile number
- `source` - Lead source (mapped from Indiamart query type)
- `company_name` - Organization name
- `state`, `country`, `city` - Location fields
- `query_id_cf` - Custom field for Indiamart Query ID
- `notes` - Child table for notes
- `lead_owner` - Assigned user
- `status` - Lead status

**Related Records:**
- **Address:** Linked via `links` child table
- **Opportunity:** Created for repeat leads with status "Converted" or "Quotation"

### 2.3 Standalone CRM App Structure

**CRM Lead Doctype (`CRM Lead`):**

**Key Fields:**
- `lead_name` - Full name (auto-generated)
- `first_name` - Required field
- `last_name` - Optional
- `middle_name` - Optional
- `email` - Email address (not `email_id`)
- `mobile_no` - Mobile number
- `phone` - Phone number
- `source` - Link to `CRM Lead Source` (not `Lead Source`)
- `organization` - Organization name (not `company_name`)
- `website` - Website URL
- `territory` - Link to `CRM Territory`
- `industry` - Link to `CRM Industry`
- `status` - Link to `CRM Lead Status` (default: "New")
- `lead_owner` - Link to User
- `salutation` - Salutation
- `gender` - Gender
- `job_title` - Job title
- `naming_series` - "CRM-LEAD-.YYYY.-"

**Notable Differences:**
- No built-in `notes` child table - uses separate `FCRM Note` doctype
- No direct address fields - uses Contact/Organization pattern
- Uses `organization` instead of `company_name`
- Uses `email` instead of `email_id`
- Status is a Link field to `CRM Lead Status`, not a Select field

**Related Records:**
- **FCRM Note:** Separate doctype with fields:
  - `title` - Note title
  - `content` - HTML content
  - `reference_doctype` - "CRM Lead"
  - `reference_docname` - Lead name
- **Contact:** Created via `create_contact()` method
- **CRM Organization:** Created via `create_organization()` method
- **CRM Deal:** Created via `convert_to_deal()` method (equivalent to Opportunity)

---

## 3. Detailed Mapping Analysis

### 3.1 Field Mapping: ERPNext Lead → CRM Lead

| ERPNext Lead Field | CRM Lead Field | Notes |
|-------------------|----------------|-------|
| `first_name` | `first_name` | Direct mapping ✓ |
| `lead_name` | `lead_name` | Auto-generated in CRM, can be set |
| `email_id` | `email` | **Field name change** |
| `mobile_no` | `mobile_no` | Direct mapping ✓ |
| `company_name` | `organization` | **Field name change** |
| `source` | `source` | **Different doctype:** `Lead Source` → `CRM Lead Source` |
| `state` | - | No direct field, handled via Contact/Organization |
| `country` | - | No direct field, handled via Contact/Organization |
| `city` | - | No direct field, handled via Contact/Organization |
| `query_id_cf` | **NEW CUSTOM FIELD** | Need to create custom field |
| `notes` (child table) | **FCRM Note** (separate doctype) | **Architecture change** |
| `lead_owner` | `lead_owner` | Direct mapping ✓ |
| `status` | `status` | **Different doctype:** Select → Link to `CRM Lead Status` |

### 3.2 Settings Mapping

| Indiamart Settings Field | Target Doctype | Notes |
|-------------------------|----------------|-------|
| `default_lead_owner` | User | No change |
| `direct_lead_source` | `CRM Lead Source` | Change from `Lead Source` |
| `buy_lead_source` | `CRM Lead Source` | Change from `Lead Source` |
| `call_lead_source` | `CRM Lead Source` | Change from `Lead Source` |
| `default_opportunity_sales_stage` | **CRM Deal Status** | Change from `Sales Stage` to `CRM Deal Status` |

### 3.3 Related Records Mapping

| ERPNext Pattern | CRM Pattern | Implementation |
|----------------|-------------|----------------|
| Address linked to Lead | Contact with address fields | Use `create_contact()` method |
| Opportunity from Lead | CRM Deal from Lead | Use `convert_to_deal()` method |
| Notes as child table | FCRM Note as separate doc | Create separate FCRM Note records |

---

## 4. Tasks to Achieve Migration

### 4.1 Prerequisites
- [ ] Ensure standalone CRM app is installed
- [ ] Verify `CRM Lead Source` doctype exists
- [ ] Verify `CRM Lead Status` doctype exists with "New", "Lead", "Qualified" statuses
- [ ] Verify `CRM Deal Status` doctype exists

### 4.2 Configuration Changes

#### Task 1: Update Indiamart Settings Doctype
**File:** `indiamart_erpnext_integration/doctype/indiamart_settings/indiamart_settings.json`

**Changes:**
1. Change `direct_lead_source` options from `Lead Source` to `CRM Lead Source`
2. Change `buy_lead_source` options from `Lead Source` to `CRM Lead Source`
3. Change `call_lead_source` options from `Lead Source` to `CRM Lead Source`
4. Change `default_opportunity_sales_stage` options from `Sales Stage` to `CRM Deal Status`
5. Update field descriptions to reflect CRM app usage

#### Task 2: Create Custom Field for CRM Lead
**File:** `indiamart_erpnext_integration/fixtures/custom_field.json` (create if not exists)

**Changes:**
1. Create custom field `query_id_cf` for `CRM Lead` doctype
   - Field Type: Data
   - Label: "Indiamart Query ID"
   - Unique: Yes
   - Read Only: Yes
2. Update fixtures in `hooks.py` to include new custom field

### 4.3 Core Logic Changes

#### Task 3: Update Controller Imports
**File:** `indiamart_erpnext_controller.py`

**Line 13 - Change:**
```python
# OLD
from erpnext.crm.doctype.lead.lead import make_opportunity

# NEW
from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal
```

#### Task 4: Modify Lead Creation Function
**File:** `indiamart_erpnext_controller.py`
**Function:** `make_erpnext_lead_from_inidamart()` (Lines 175-323)

**Changes Required:**

**4.1 Update Doctype References (Line 187, 191, 202, etc.)**
```python
# OLD
lead_name = frappe.db.get_value("Lead", {"query_id_cf": lead_values.get('UNIQUE_QUERY_ID')})
lead_name = frappe.db.get_value("Lead", {"mobile_no": check_duplicate_mobile_no})
lead_name = frappe.db.get_value("Lead", {"email_id": email_id})

# NEW
lead_name = frappe.db.get_value("CRM Lead", {"query_id_cf": lead_values.get('UNIQUE_QUERY_ID')})
lead_name = frappe.db.get_value("CRM Lead", {"mobile_no": check_duplicate_mobile_no})
lead_name = frappe.db.get_value("CRM Lead", {"email": email_id})  # Note: email_id → email
```

**4.2 Update Source Field References (Lines 213-219)**
```python
# OLD
source = frappe.db.get_single_value('Indiamart Settings', 'direct_lead_source')

# NEW - Add validation
source = frappe.db.get_single_value('Indiamart Settings', 'direct_lead_source')
# Verify source exists in CRM Lead Source
if source and not frappe.db.exists('CRM Lead Source', source):
    source = None  # Or create default source
```

**4.3 Replace Lead Creation Logic (Lines 261-287)**
```python
# OLD
lead = frappe.new_doc('Lead')
lead_value_dict = {
    "lead_name": lead_values.get('SENDER_NAME'),
    "first_name": lead_values.get('SENDER_NAME'),
    "email_id": email_id,
    "mobile_no": mobile_no,
    "source": source or '',
    "company_name": company_name,
    "state": state,
    "country": country,
    "city": city or 'Not specified',
    "query_id_cf": lead_values.get('UNIQUE_QUERY_ID'),
    'lead_owner': lead_owner
}
lead.update(lead_value_dict)
lead.append('notes', {'note': notes_html})

# NEW
lead = frappe.new_doc('CRM Lead')
lead_value_dict = {
    "first_name": lead_values.get('SENDER_NAME'),  # Required field
    "email": email_id,  # Changed from email_id
    "mobile_no": mobile_no,
    "source": source or '',
    "organization": company_name,  # Changed from company_name
    "query_id_cf": lead_values.get('UNIQUE_QUERY_ID'),
    'lead_owner': lead_owner,
    'status': 'New'  # Set default status
}
lead.update(lead_value_dict)
# Notes are handled separately - see Task 5
```

**4.4 Remove Address Creation Logic (Lines 288-305)**
```python
# OLD - Direct address creation
address = frappe.get_doc({
    "doctype": "Address",
    "address_title": address_title or 'Other',
    ...
})
address.insert()

# NEW - Use CRM's contact creation
# Address will be handled via Contact creation if needed
# Or store in custom fields on CRM Lead
# Decision: Store address info in FCRM Note for now
```

#### Task 5: Implement Note Creation for CRM
**File:** `indiamart_erpnext_controller.py`
**New Function:** Add after line 310

```python
def create_crm_note(lead_name, notes_html, title="Indiamart Lead Details"):
    """
    Create FCRM Note linked to CRM Lead
    """
    note = frappe.new_doc('FCRM Note')
    note.update({
        'title': title,
        'content': notes_html,
        'reference_doctype': 'CRM Lead',
        'reference_docname': lead_name
    })
    note.flags.ignore_permissions = True
    note.insert()
    return note.name
```

**Update Lead Creation to Use Notes:**
```python
# After lead.save() (around line 287)
lead.save()

# Create note with lead details
create_crm_note(lead.name, notes_html, "Indiamart Lead Details")

# If address exists, create another note with address
if address:
    address_html = f"<div><b>Address:</b></div><div>{address}</div>"
    address_html += f"<div>City: {city}</div><div>State: {state}</div>"
    address_html += f"<div>Pincode: {pincode}</div><div>Country: {country}</div>"
    create_crm_note(lead.name, address_html, "Address Information")
```

#### Task 6: Update Existing Lead Update Function
**File:** `indiamart_erpnext_controller.py`
**Function:** `update_existing_lead()` (Lines 324-388)

**Changes Required:**

**6.1 Update Doctype References**
```python
# OLD (Line 326)
lead_status = frappe.db.get_value('Lead', lead_name, 'status')

# NEW
lead_status = frappe.db.get_value('CRM Lead', lead_name, 'status')
```

**6.2 Update Status Check Logic (Line 328)**
```python
# OLD
if lead_status not in ['Converted', 'Quotation']:

# NEW - Check against CRM Lead Status
if lead_status not in ['Qualified', 'Converted']:  # Adjust based on CRM statuses
```

**6.3 Replace Notes Update Logic (Lines 340-352)**
```python
# OLD
lead = frappe.get_doc('Lead', lead_name)
lead.reload()
if lead.notes and len(lead.notes) > 0:
    lead.get("notes")[0].note = lead.notes[0].note + notes_html
else:
    lead.append('notes', {'note': notes_html})
lead.save()

# NEW
lead = frappe.get_doc('CRM Lead', lead_name)
lead.reload()
# Create new note instead of appending
create_crm_note(lead.name, notes_html, "New Requirement")
lead.query_id_cf = lead_values.get('UNIQUE_QUERY_ID')
lead.status = 'Lead'  # Update status
lead.save()
```

**6.4 Replace Opportunity Creation with Deal Creation (Lines 367-387)**
```python
# OLD
opportunity = make_opportunity(source_name=lead_name)
opportunity.flags.ignore_mandatory = True
opportunity.flags.ignore_permissions = True
opportunity.to_discuss = to_discuss_html
opportunity.sales_stage = frappe.db.get_single_value('Indiamart Settings', 'default_opportunity_sales_stage')
opportunity.save()

# NEW
# First convert lead to deal
deal_name = convert_to_deal(
    lead=lead_name,
    doc=None,
    deal=None,
    existing_contact=None,
    existing_organization=None
)

# Update deal with Indiamart info
deal = frappe.get_doc('CRM Deal', deal_name)
deal.flags.ignore_mandatory = True
deal.flags.ignore_permissions = True

# Get default deal status from settings
default_status = frappe.db.get_single_value('Indiamart Settings', 'default_opportunity_sales_stage')
if default_status and frappe.db.exists('CRM Deal Status', default_status):
    deal.status = default_status

deal.save()

# Create note on deal with requirement details
create_crm_note(deal_name, to_discuss_html, "New Requirement")

# Update lead with deal reference
lead = frappe.get_doc('CRM Lead', lead_name)
opportunity_html = f'<br><br><div><B>New Deal {deal_name} was created</B></div>'
create_crm_note(lead.name, opportunity_html, "Deal Created")
```

#### Task 7: Update Hooks Configuration
**File:** `hooks.py`

**Changes:**
```python
# OLD (Line 35)
doctype_js = {
    "Lead": "public/js/lead.js",
    "Integration Request": "public/js/integration_request.js"
}

# NEW
doctype_js = {
    "CRM Lead": "public/js/crm_lead.js",  # Rename file
    "Integration Request": "public/js/integration_request.js"
}

# Update fixtures (Lines 197-201)
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["name", "in", ["CRM Lead-query_id_cf"]]]  # Changed from Lead
    }
]
```

---

## 5. Where to Change (File-by-File Summary)

### 5.1 Configuration Files

| File | Changes | Priority |
|------|---------|----------|
| `indiamart_settings.json` | Update Link field options | High |
| `hooks.py` | Update doctype_js, fixtures | High |
| `fixtures/custom_field.json` | Add CRM Lead custom field | High |

### 5.2 Python Files

| File | Function | Changes | Lines |
|------|----------|---------|-------|
| `indiamart_erpnext_controller.py` | Imports | Change import from erpnext to crm | 13 |
| | `make_erpnext_lead_from_inidamart()` | Update all Lead → CRM Lead references | 175-323 |
| | | Change email_id → email | Multiple |
| | | Change company_name → organization | Multiple |
| | | Replace notes child table with FCRM Note | 284 |
| | | Remove address creation logic | 288-305 |
| | `update_existing_lead()` | Update Lead → CRM Lead | 324-388 |
| | | Replace notes with FCRM Note | 340-352 |
| | | Replace make_opportunity with convert_to_deal | 367-387 |
| | NEW: `create_crm_note()` | Add new function | After 310 |

### 5.3 JavaScript Files

| File | Changes | Priority |
|------|---------|----------|
| `public/js/lead.js` | Rename to `crm_lead.js`, update references | Medium |

---

## 6. How to Change (Implementation Details)

### 6.1 Development Workflow

1. **Setup Development Environment**
   ```bash
   cd frappe-bench
   bench get-app crm  # If not already installed
   bench --site [site-name] install-app crm
   ```

2. **Create Feature Branch**
   ```bash
   cd apps/indiamart_erpnext_integration
   git checkout -b feature/crm-migration
   ```

3. **Make Changes in Order:**
   - Step 1: Update configuration files (Settings, Hooks)
   - Step 2: Create custom fields
   - Step 3: Update controller imports
   - Step 4: Modify lead creation logic
   - Step 5: Update existing lead logic
   - Step 6: Test thoroughly

4. **Testing After Each Change**
   ```bash
   bench --site [site-name] migrate
   bench --site [site-name] clear-cache
   bench restart
   ```

### 6.2 Detailed Implementation Steps

#### Step 1: Update Indiamart Settings
```bash
# Edit the JSON file
nano indiamart_erpnext_integration/indiamart_erpnext_integration/doctype/indiamart_settings/indiamart_settings.json
```

**Find and replace:**
- `"options": "Lead Source"` → `"options": "CRM Lead Source"`
- `"options": "Sales Stage"` → `"options": "CRM Deal Status"`

#### Step 2: Create Custom Field Fixture
```bash
# Create fixtures directory if not exists
mkdir -p indiamart_erpnext_integration/fixtures

# Create custom_field.json
nano indiamart_erpnext_integration/fixtures/custom_field.json
```

**Content:**
```json
[
    {
        "doctype": "Custom Field",
        "dt": "CRM Lead",
        "fieldname": "query_id_cf",
        "fieldtype": "Data",
        "label": "Indiamart Query ID",
        "unique": 1,
        "read_only": 1,
        "insert_after": "lead_name"
    }
]
```

#### Step 3: Update Controller File

**Open file:**
```bash
nano indiamart_erpnext_integration/indiamart_erpnext_controller.py
```

**Make changes in this order:**

1. **Update import (Line 13):**
   - Remove: `from erpnext.crm.doctype.lead.lead import make_opportunity`
   - Add: `from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal`

2. **Add helper function after line 173:**
   ```python
   def create_crm_note(lead_name, notes_html, title="Indiamart Lead Details"):
       note = frappe.new_doc('FCRM Note')
       note.update({
           'title': title,
           'content': notes_html,
           'reference_doctype': 'CRM Lead',
           'reference_docname': lead_name
       })
       note.flags.ignore_permissions = True
       note.insert()
       return note.name
   ```

3. **Update function `make_erpnext_lead_from_inidamart()` starting line 175:**
   - Search and replace all `"Lead"` with `"CRM Lead"`
   - Change `email_id` to `email` in all get_value calls
   - Update lead creation dict (lines 262-282)
   - Replace notes append with create_crm_note call

4. **Update function `update_existing_lead()` starting line 324:**
   - Change `'Lead'` to `'CRM Lead'`
   - Update status checks
   - Replace notes logic with create_crm_note
   - Replace make_opportunity with convert_to_deal

### 6.3 Code Review Checklist

Before committing changes, verify:

- [ ] All `"Lead"` references changed to `"CRM Lead"`
- [ ] All `email_id` changed to `email`
- [ ] All `company_name` changed to `organization`
- [ ] All `Lead Source` changed to `CRM Lead Source`
- [ ] Notes child table replaced with FCRM Note creation
- [ ] Opportunity creation replaced with Deal creation
- [ ] Custom field fixture created
- [ ] Hooks updated
- [ ] Import statements updated
- [ ] No syntax errors (run `python -m py_compile indiamart_erpnext_controller.py`)

---

## 7. Testing Plan

### 7.1 Unit Test Plan

#### Test 1: Custom Field Creation
**Objective:** Verify custom field `query_id_cf` exists on CRM Lead

**Steps:**
1. Run migration: `bench --site [site] migrate`
2. Check field exists:
   ```python
   frappe.get_meta('CRM Lead').get_field('query_id_cf')
   ```
3. Verify field properties (unique, read_only)

**Expected Result:** Field exists with correct properties

---

#### Test 2: Lead Source Mapping
**Objective:** Verify Indiamart Settings accepts CRM Lead Source

**Steps:**
1. Navigate to Indiamart Settings
2. Try to select a value for Direct Lead Source
3. Verify dropdown shows CRM Lead Source options

**Expected Result:** Only CRM Lead Source options visible

---

#### Test 3: New Lead Creation from Indiamart
**Objective:** Verify new lead creation works with CRM Lead

**Test Data:**
```python
lead_values = {
    'UNIQUE_QUERY_ID': 'TEST123456',
    'SENDER_NAME': 'Test User',
    'SENDER_EMAIL': 'test@example.com',
    'SENDER_MOBILE': '+91-9876543210',
    'SENDER_COMPANY': 'Test Company',
    'SENDER_STATE': 'Maharashtra',
    'SENDER_CITY': 'Mumbai',
    'SENDER_COUNTRY_ISO': 'IN',
    'QUERY_PRODUCT_NAME': 'Test Product',
    'QUERY_MESSAGE': 'Test inquiry',
    'QUERY_TIME': '2024-01-01 10:00:00',
    'QUERY_TYPE': 'W'
}
```

**Steps:**
1. Create test Indiamart Lead record
2. Call `make_erpnext_lead_from_inidamart(lead_values, 'TEST-IND-001')`
3. Verify CRM Lead created:
   ```python
   lead = frappe.get_doc('CRM Lead', {'query_id_cf': 'TEST123456'})
   assert lead.first_name == 'Test User'
   assert lead.email == 'test@example.com'
   assert lead.mobile_no == '+91-9876543210'
   assert lead.organization == 'Test Company'
   ```
4. Verify FCRM Note created:
   ```python
   notes = frappe.get_all('FCRM Note', 
       filters={'reference_docname': lead.name},
       fields=['title', 'content'])
   assert len(notes) > 0
   ```

**Expected Result:** 
- CRM Lead created with correct field mappings
- FCRM Note created with lead details
- Indiamart Lead status = "Completed"

---

#### Test 4: Duplicate Lead Detection (Mobile)
**Objective:** Verify duplicate detection by mobile number

**Steps:**
1. Create initial lead with mobile '+91-9876543210'
2. Try to create another lead with same mobile
3. Verify existing lead is updated, not duplicated
4. Verify new FCRM Note created with "New Requirement"

**Expected Result:** 
- No duplicate CRM Lead created
- Existing lead updated with new query_id_cf
- New note added to existing lead

---

#### Test 5: Duplicate Lead Detection (Email)
**Objective:** Verify duplicate detection by email

**Steps:**
1. Create initial lead with email 'test@example.com'
2. Try to create another lead with same email (different mobile)
3. Verify existing lead is updated

**Expected Result:** Same as Test 4

---

#### Test 6: Repeat Lead - Deal Creation
**Objective:** Verify deal creation for repeat leads with "Qualified" status

**Steps:**
1. Create CRM Lead with status "Qualified"
2. Submit new Indiamart inquiry for same mobile
3. Verify CRM Deal created
4. Verify deal has correct status from settings
5. Verify note created on deal

**Expected Result:**
- CRM Deal created via `convert_to_deal()`
- Deal status matches `default_opportunity_sales_stage` setting
- Note created on deal with requirement details
- Note created on lead referencing deal

---

#### Test 7: API Integration Test
**Objective:** Verify full API to lead creation flow

**Steps:**
1. Enable Indiamart Settings
2. Mock API response with test data
3. Call `auto_pull_indiamart_leads()`
4. Verify Integration Request created
5. Verify Indiamart Lead created
6. Verify CRM Lead created
7. Verify FCRM Notes created

**Expected Result:** Complete flow works end-to-end

---

### 7.2 Integration Test Plan

#### Integration Test 1: Scheduler Job
**Objective:** Verify cron job runs successfully

**Steps:**
1. Enable Indiamart Settings
2. Set valid API credentials (test environment)
3. Wait for scheduler to run (6 minutes)
4. Check Integration Request log
5. Verify leads created in CRM Lead

**Expected Result:** Leads automatically pulled and created

---

#### Integration Test 2: Manual Pull
**Objective:** Verify manual lead pull functionality

**Steps:**
1. Navigate to Indiamart Settings
2. Click "Manual Pull Leads" button
3. Enter date range
4. Submit
5. Verify leads created

**Expected Result:** Leads pulled for specified date range

---

### 7.3 Manual Testing Checklist

#### Pre-requisites
- [ ] CRM app installed
- [ ] Indiamart Settings configured with test credentials
- [ ] At least one CRM Lead Source created
- [ ] At least one CRM Deal Status created

#### Test Scenarios

**Scenario 1: Fresh Lead Creation**
1. Trigger manual pull or wait for scheduler
2. Navigate to CRM Lead list
3. Open newly created lead
4. Verify all fields populated correctly
5. Check Notes tab - verify notes created
6. Verify query_id_cf field has Indiamart Query ID

**Scenario 2: Duplicate Lead Handling**
1. Create test lead manually in CRM
2. Trigger Indiamart pull with same mobile/email
3. Verify no duplicate created
4. Verify new note added to existing lead

**Scenario 3: Deal Creation**
1. Create CRM Lead with status "Qualified"
2. Trigger Indiamart pull with same contact
3. Navigate to CRM Deal list
4. Verify new deal created
5. Verify deal linked to lead
6. Verify notes on both lead and deal

**Scenario 4: Error Handling**
1. Disable CRM app temporarily
2. Trigger Indiamart pull
3. Verify error logged in Integration Request
4. Verify error notification sent

---

### 7.4 Automated Test Script

**File:** `indiamart_erpnext_integration/tests/test_crm_integration.py`

```python
import frappe
import unittest
from indiamart_erpnext_integration.indiamart_erpnext_controller import (
    make_erpnext_lead_from_inidamart,
    update_existing_lead,
    create_crm_note
)

class TestCRMIntegration(unittest.TestCase):
    
    def setUp(self):
        """Setup test data"""
        self.test_lead_values = {
            'UNIQUE_QUERY_ID': 'TEST' + frappe.generate_hash(length=10),
            'SENDER_NAME': 'Test User',
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_MOBILE': '+91-9876543210',
            'SENDER_COMPANY': 'Test Company',
            'QUERY_TYPE': 'W',
            'QUERY_PRODUCT_NAME': 'Test Product',
            'QUERY_MESSAGE': 'Test inquiry',
            'QUERY_TIME': '2024-01-01 10:00:00'
        }
    
    def tearDown(self):
        """Cleanup test data"""
        # Delete test leads
        frappe.db.delete('CRM Lead', {'query_id_cf': ['like', 'TEST%']})
        frappe.db.delete('FCRM Note', {'title': ['like', '%Test%']})
        frappe.db.commit()
    
    def test_create_crm_note(self):
        """Test FCRM Note creation"""
        # Create test lead
        lead = frappe.new_doc('CRM Lead')
        lead.first_name = 'Test'
        lead.insert(ignore_permissions=True)
        
        # Create note
        note_name = create_crm_note(lead.name, '<p>Test content</p>', 'Test Note')
        
        # Verify
        note = frappe.get_doc('FCRM Note', note_name)
        self.assertEqual(note.reference_docname, lead.name)
        self.assertEqual(note.title, 'Test Note')
    
    def test_new_lead_creation(self):
        """Test new CRM Lead creation from Indiamart"""
        # Create Indiamart Lead
        indiamart_lead = frappe.new_doc('Indiamart Lead')
        indiamart_lead.query_id = self.test_lead_values['UNIQUE_QUERY_ID']
        indiamart_lead.insert(ignore_permissions=True)
        
        # Create CRM Lead
        result = make_erpnext_lead_from_inidamart(
            self.test_lead_values,
            indiamart_lead.name
        )
        
        # Verify
        lead = frappe.get_doc('CRM Lead', {'query_id_cf': self.test_lead_values['UNIQUE_QUERY_ID']})
        self.assertEqual(lead.first_name, 'Test User')
        self.assertEqual(lead.email, 'test@example.com')
        self.assertEqual(lead.organization, 'Test Company')
        
        # Verify note created
        notes = frappe.get_all('FCRM Note', 
            filters={'reference_docname': lead.name})
        self.assertGreater(len(notes), 0)
    
    def test_duplicate_mobile_detection(self):
        """Test duplicate detection by mobile"""
        # Create first lead
        lead1 = frappe.new_doc('CRM Lead')
        lead1.first_name = 'First'
        lead1.mobile_no = '+91-9876543210'
        lead1.insert(ignore_permissions=True)
        
        # Try to create duplicate
        indiamart_lead = frappe.new_doc('Indiamart Lead')
        indiamart_lead.query_id = self.test_lead_values['UNIQUE_QUERY_ID']
        indiamart_lead.insert(ignore_permissions=True)
        
        result = make_erpnext_lead_from_inidamart(
            self.test_lead_values,
            indiamart_lead.name
        )
        
        # Verify no duplicate
        leads = frappe.get_all('CRM Lead', 
            filters={'mobile_no': '+91-9876543210'})
        self.assertEqual(len(leads), 1)
        
        # Verify note added
        notes = frappe.get_all('FCRM Note',
            filters={'reference_docname': lead1.name})
        self.assertGreater(len(notes), 0)

# Run tests
# bench --site [site-name] run-tests --app indiamart_erpnext_integration --module test_crm_integration
```

**To run tests:**
```bash
bench --site [site-name] run-tests --app indiamart_erpnext_integration --module test_crm_integration
```

---


---

## 9. Deployment Checklist

### Pre-Deployment
- [ ] Code review completed
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Backup created

### Deployment Steps
1. [ ] Stop scheduler: `bench --site [site] disable-scheduler`
2. [ ] Backup database: `bench --site [site] backup`
3. [ ] Pull latest code: `git pull origin feature/crm-migration`
4. [ ] Run migration: `bench --site [site] migrate`
5. [ ] Clear cache: `bench --site [site] clear-cache`
6. [ ] Restart bench: `bench restart`
7. [ ] Verify custom fields created
8. [ ] Test lead creation manually
9. [ ] Enable scheduler: `bench --site [site] enable-scheduler`
10. [ ] Monitor for 24 hours

### Post-Deployment
- [ ] Monitor Integration Request logs
- [ ] Verify leads being created
- [ ] Check error logs
- [ ] Verify notes being created
- [ ] Test deal creation for repeat leads

---

## 10. Appendix

### A. Reference Links
- [Frappe CRM Documentation](https://docs.frappe.io/crm)
- [Indiamart API Documentation](https://help.indiamart.com/knowledge-base/lms-crm-integration-v2/)
- [Frappe Framework Documentation](https://frappeframework.com/docs)

### B. Glossary
- **CRM Lead:** Lead doctype in standalone CRM app
- **ERPNext Lead:** Lead doctype in ERPNext core
- **FCRM Note:** Note doctype in CRM app (separate from lead)
- **CRM Deal:** Equivalent to Opportunity in ERPNext
- **Indiamart Lead:** Tracking doctype for Indiamart integration
- **Integration Request:** Log of API calls

### C. Contact Information
For questions or issues:
- Developer: [Your Name]
- Email: [Your Email]
- Repository: [Git Repository URL]

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-02  
**Author:** Antigravity AI Assistant
