from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.integrations.utils import create_request_log,make_post_request
from frappe.utils import get_datetime,now_datetime,format_datetime,cstr
from datetime import timedelta
import datetime
from frappe.utils.password import get_decrypted_password
from frappe.model.document import Document
import json
from six import string_types
import traceback,sys



# manually pull leads for given time frame
@frappe.whitelist()
def manual_pull_indiamart_leads(start_time,end_time):
	try:
		indiamart_settings=get_indiamart_configuration()
		if indiamart_settings!='disabled':
			api_url,now_api_call_time=get_indiamart_api_url(indiamart_settings,start_time,end_time)
			if api_url:
				fetch_indiamart_data_and_make_integration_request(api_url,now_api_call_time)
	except Exception as e:
		title=_('Indiamart Error')
		seperator = "--" * 50
		error = "\n".join([format_datetime(now_datetime(),'d-MMM-y  HH:mm:ss'), "manual_pull_indiamart_leads",str(sys.exc_info()[1]), seperator,frappe.get_traceback()])
		frappe.log_error(message=error, title=title)

# entry point for scheduler 
@frappe.whitelist()
def auto_pull_indiamart_leads():
	try:
		indiamart_settings=get_indiamart_configuration()
		if indiamart_settings!='disabled':
			api_url,now_api_call_time=get_indiamart_api_url(indiamart_settings)
			if api_url:
				fetch_indiamart_data_and_make_integration_request(api_url,now_api_call_time)
	except Exception as e:
		title=_('Indiamart Error')
		seperator = "--" * 50
		error = "\n".join([format_datetime(now_datetime(),'d-MMM-y  HH:mm:ss'), "auto_pull_indiamart_leads",str(sys.exc_info()[1]), seperator,frappe.get_traceback()])
		frappe.log_error(message=error, title=title)


def get_indiamart_configuration():
	if frappe.db.get_single_value("Indiamart Settings", "enabled"):
		indiamart_settings = frappe.get_doc("Indiamart Settings")
		return {
			"glusr_mobile": indiamart_settings.glusr_mobile,
			"glusr_mobile_key": indiamart_settings.glusr_mobile_key,
			"last_api_call_time": indiamart_settings.last_api_call_time
		}
	return "disabled"

def get_indiamart_api_url(indiamart_settings,start_time=None,end_time=None):
	URL_DATETIME_FORMAT = 'd-MMM-yHH:mm:ss'
	# INDIAMART_URL = 'https://mapi.indiamart.com/wservce/enquiry/listing/GLUSR_MOBILE/{0}/GLUSR_MOBILE_KEY/{1}/Start_Time/{2}/End_Time/{3}/'
	# https://mapi.indiamart.com/wservce/crm/crmListing/v2/?glusr_crm_key=1mRyzE7ll43bDTvev4nCI7luMoFPDlTQ=&start_time=4-Jan-202415:38:44&end_time=4-Jan-202415:46:41
	INDIAMART_URL = 'https://mapi.indiamart.com/wservce/crm/crmListing/v2/?glusr_crm_key={1}&start_time={2}&end_time={3}'

	#  scheduler flow
	if start_time==None:
		# set start time as minus 5 minutes the last api call time
		print("indiamart_settings.get('last_api_call_time')",indiamart_settings.get('last_api_call_time'))
		if indiamart_settings.get('last_api_call_time'):
			# Look back 24 hours to ensure no leads are missed due to IndiaMART sync delays
			start_time = get_datetime(indiamart_settings.get('last_api_call_time')) - datetime.timedelta(minutes=7)
		else:
			# If no last call time, look back 24 hours
			start_time = now_datetime() - datetime.timedelta(minutes=7)

		start_time=format_datetime(start_time,URL_DATETIME_FORMAT)
		now_api_call_time=now_datetime()
		end_time=format_datetime(now_api_call_time,URL_DATETIME_FORMAT)
	# manual pull flow
	else:
		start_time=format_datetime(start_time,URL_DATETIME_FORMAT)
		end_time=format_datetime(end_time,URL_DATETIME_FORMAT)
		# we don't change last call time as it is a manual attempt
		now_api_call_time=indiamart_settings.get('last_api_call_time') or now_datetime()
	#  to do : put in config
	print('start_time',start_time,'end_time',end_time)
	api_url = INDIAMART_URL.format(
				indiamart_settings.get('glusr_mobile'),
				get_decrypted_password('Indiamart Settings','Indiamart Settings','glusr_mobile_key'),
				start_time,
				end_time)
	print("--- GENERATED API URL ---")
	print("URL:", api_url)
	print("Start Time:", start_time)
	print("End Time:", end_time)
	print("-------------------------")
	return api_url,now_api_call_time



def fetch_indiamart_data_and_make_integration_request(api_url,now_api_call_time):
	valid_error_messages=['There are no leads in the given time duration. Please try for a different duration.',
												'It is advised to hit this API once in every 5 minutes, but it seems that you have crossed this limit. Please try again after 5 minutes.']
    # v2
	# how to test, 
	# (a)uncomment + comment response 
	# (b) enable settings 
	# (c) bench --site rfs execute indiamart_erpnext_integration.indiamart_erpnext_controller.auto_pull_indiamart_leads
	# response={'CODE': 200, 'STATUS': 'SUCCESS', 'MESSAGE': '', 'TOTAL_RECORDS': 2, 'RESPONSE': [{'UNIQUE_QUERY_ID': '2243859917', 'QUERY_TYPE': 'W', 'QUERY_TIME': '2022-09-17 09:34:45', 'SENDER_NAME': 'Shuaib', 'SENDER_MOBILE': '+91-8384869226', 'SENDER_EMAIL': '', 'SENDER_COMPANY': '', 'SENDER_ADDRESS': 'Dehradun, Uttarakhand', 'SENDER_CITY': 'Dehradun', 'SENDER_STATE': 'Uttarakhand', 'SENDER_COUNTRY_ISO': 'IN', 'SENDER_MOBILE_ALT': '', 'SENDER_PHONE': '', 'SENDER_PHONE_ALT': '', 'SENDER_EMAIL_ALT': '', 'QUERY_PRODUCT_NAME': 'Fuel Pressure Regulator Sensor', 'QUERY_MESSAGE': 'I want to buy Fuel Pressure Regulator Sensor.\r\rBefore purchasing I would like to know the price details.\r\rKindly send me price and other details.<br> Quantity :   1<br> Quantity Unit :   piece<br> Probable Order Value :   Rs. 3,000 to 10,000<br> Probable Requirement Type :   Business Use<br>Preferred Location: Suppliers from Local Area will be Preferred<br>', 'CALL_DURATION': '', 'RECEIVER_MOBILE': ''}, {'UNIQUE_QUERY_ID': '2243945858', 'QUERY_TYPE': 'W', 'QUERY_TIME': '2022-09-17 10:56:07', 'SENDER_NAME': 'Mamilla Ganga Shekhar', 'SENDER_MOBILE': '+91-9100843314', 'SENDER_EMAIL': 'gangadharmamilla@gmail.com', 'SENDER_COMPANY': 'VS Automation', 'SENDER_ADDRESS': 'KTR Colony, Hyderabad, Telangana,         500072', 'SENDER_CITY': 'Hyderabad', 'SENDER_STATE': 'Telangana', 'SENDER_COUNTRY_ISO': 'IN', 'SENDER_MOBILE_ALT': '', 'SENDER_PHONE': '', 'SENDER_PHONE_ALT': '', 'SENDER_EMAIL_ALT': '', 'QUERY_PRODUCT_NAME': 'Capacitive Proximity Sensors', 'QUERY_MESSAGE': 'I want to buy Capacitive Proximity Sensors.<br> Model :   Prk3pl1.btt3x4t<br> Quantity :   6<br> Quantity Unit :   piece<br> Sensing Distance :   0-0.3 Meter<br> Probable Order Value :   Rs. 3,000 to 10,000<br> Probable Requirement Type :   Business Use<br>Preferred Location: Suppliers from all over India can contact<br>', 'CALL_DURATION': '', 'RECEIVER_MOBILE': ''}]}
	# response={'CODE': 200, 'STATUS': 'SUCCESS', 'MESSAGE': '', 'TOTAL_RECORDS': 2, 'RESPONSE': [{"UNIQUE_QUERY_ID": "2643097564", "QUERY_TYPE": "W", "QUERY_TIME": "2023-12-29 18:14:37", "SENDER_NAME": "Rajendra Singh Rathore", "SENDER_MOBILE": "+91-9680852019", "SENDER_EMAIL": "rajendarsingh02218@gmail.com", "SUBJECT": "Requirement for 550 W Mono PERC PV Solar Module", "SENDER_COMPANY": "Mumbai Fashions", "SENDER_ADDRESS": "6/682, Ground Floor, Ernakulam, Kerala,         683513", "SENDER_CITY": "Ernakulam", "SENDER_STATE": "Kerala", "SENDER_PINCODE": "683513", "SENDER_COUNTRY_ISO": "IN", "SENDER_MOBILE_ALT": "", "SENDER_PHONE": "", "SENDER_PHONE_ALT": "", "SENDER_EMAIL_ALT": "", "QUERY_PRODUCT_NAME": "550 W Mono PERC PV Solar Module", "QUERY_MESSAGE": "I am interested in 550 W Mono PERC PV Solar Module<br>", "QUERY_MCAT_NAME": "Monocrystalline Solar Panel", "CALL_DURATION": "", "RECEIVER_MOBILE": ""},{"UNIQUE_QUERY_ID": "154427286", "QUERY_TYPE": "P", "QUERY_TIME": "2024-01-01 20:36:42", "SENDER_NAME": "Anirudhya", "SENDER_MOBILE": "+91-7063035636", "SENDER_EMAIL": "", "SUBJECT": "Buyer Call", "SENDER_COMPANY": "Mayadevi Enterprise Banerjee And Sons Pvt Limited", "SENDER_ADDRESS": "Purulia, West Bengal", "SENDER_CITY": "Purulia", "SENDER_STATE": "West Bengal", "SENDER_PINCODE": "", "SENDER_COUNTRY_ISO": "IN", "SENDER_MOBILE_ALT": "", "SENDER_PHONE": "", "SENDER_PHONE_ALT": "", "SENDER_EMAIL_ALT": "", "QUERY_PRODUCT_NAME": "", "QUERY_MESSAGE": "", "QUERY_MCAT_NAME": "", "CALL_DURATION": "105", "RECEIVER_MOBILE": "8048956627"},{"UNIQUE_QUERY_ID": "2646648941", "QUERY_TYPE": "W", "QUERY_TIME": "2024-01-03 14:08:55", "SENDER_NAME": "Himanshu Aggarwal", "SENDER_MOBILE": "+91-9811610456", "SENDER_EMAIL": "sidaggarwal91@gmail.com", "SUBJECT": "Requirement for 1 hp Amrut Energy Submersible Pump", "SENDER_COMPANY": "", "SENDER_ADDRESS": "New Delhi, Delhi", "SENDER_CITY": "New Delhi", "SENDER_STATE": "Delhi", "SENDER_PINCODE": "", "SENDER_COUNTRY_ISO": "IN", "SENDER_MOBILE_ALT": "", "SENDER_PHONE": "", "SENDER_PHONE_ALT": "", "SENDER_EMAIL_ALT": "", "QUERY_PRODUCT_NAME": "1 hp Amrut Energy Submersible Pump", "QUERY_MESSAGE": "I am interested in 1 hp Amrut Energy Submersible Pump<br>", "QUERY_MCAT_NAME": "Submersible Pump", "CALL_DURATION": "", "RECEIVER_MOBILE": ""}]}
	response = make_post_request(api_url)
	if not response:
		return

	if isinstance(response, string_types):
		response = json.loads(response)	
	print("--- INDIAMART API RAW RESPONSE ---")
	print(json.dumps(response, indent=4, sort_keys=True, default=str))
	print("--- END RAW RESPONSE ---")

	response_result = []
	if response.get("RESPONSE"):
		response_result = list(response.get("RESPONSE"))
	
	print("--- PARSED RESPONSE RESULT ---")
	print(json.dumps(response_result, indent=4, sort_keys=True, default=str))
	print("------------------------------")
	data={
		'api_url':api_url
	}
	request_log_data={
		'api_url':api_url,
		"reference_doctype":"Indiamart Lead"
	}
	error=None
	output={
		'output':response_result
	}

	if response.get('MESSAGE') and response.get('MESSAGE')!="":
		error=response.get('MESSAGE')
		
	if not error:
		integration_request=create_request_log(data=frappe._dict(request_log_data),integration_type="Remote",service_name="Indiamart")
		# Log full response for debugging
		output['raw_response'] = response
		frappe.db.set_value('Integration Request', integration_request.name, 'output',json.dumps(output) )
	else:
		integration_request=create_request_log(data=frappe._dict(request_log_data),integration_type="Remote",service_name="Indiamart",error=frappe._dict({"error":error}))
		frappe.db.set_value('Integration Request', integration_request.name, 'output', json.dumps(output))

	error_message=response.get('MESSAGE')
	status=None

	if (not error_message):
		status='Queued'
	elif error_message in valid_error_messages:
		frappe.db.set_value('Integration Request', integration_request.name, 'status', 'Cancelled')
		frappe.db.set_value('Indiamart Settings','Indiamart Settings', 'last_api_call_time', now_api_call_time)
		print("--- API STATUS: NO LEADS / LIMIT EXCEEDED ---")
		print("Msg:", error_message)
		print("This is a valid response from IndiaMART indicating no data or rate limit.")
		print("---------------------------------------------")
		status='Failed'
	else: 
		frappe.db.set_value('Integration Request', integration_request.name, 'status', 'Failed')
		status='Failed'	
		# serious error. log it
		error_message=error_message+'\nIntegration Request ID :'+integration_request.name
		frappe.log_error(message=error_message, title=_('Indiamart Error'))	

	if 	status!='Failed':
		#  use response_result
		for index in range(len(response_result)):
				lead_values={}
				for key in response_result[index]:
						lead_values.update({key:response_result[index][key]})
				# make_lead_from_inidamart(lead_values)
				make_indiamart_lead_records(lead_values,integration_request.name)
		frappe.db.set_value('Integration Request', integration_request.name, 'status', 'Completed')
		frappe.db.set_value('Indiamart Settings','Indiamart Settings', 'last_api_call_time', now_api_call_time)
	return

def extract_quantity_from_message(message):
	"""
	Extracts quantity from IndiaMART message string like:
	'Quantity :   1<br> Quantity Unit :   piece<br>'
	"""
	if not message:
		return None
	
	# Regex to find 'Quantity : <value><br>' or 'Quantity : <value>' at end of line
	# Case insensitive, matching 'Quantity', optional spaces, colon, optional spaces, capturing group for value
	# Stops at <, newline, or end of string
	match = re.search(r"Quantity\s*:\s*(.*?)(?:<|\n|$)", message, re.IGNORECASE)
	if match:
		return match.group(1).strip()
	return None

def make_indiamart_lead_records(lead_values,integration_request,status='Queued',output='Not Processed'):
	existing_indiamart_lead = frappe.db.get_value("Indiamart Lead", {"query_id": lead_values.get('UNIQUE_QUERY_ID')})
	if not existing_indiamart_lead:
		indiamart_lead=frappe.new_doc('Indiamart Lead')
		indiamart_lead.query_id=lead_values.get('UNIQUE_QUERY_ID',None)
		indiamart_lead.indiamart_lead_json=json.dumps(lead_values)
		indiamart_lead.status=status
		indiamart_lead.output=output
		indiamart_lead.integration_request=integration_request
		indiamart_lead.save(ignore_permissions=True)
		return indiamart_lead.name
	return

def create_crm_note(lead_name, notes_html, title="Indiamart Lead Details", ref_doctype="CRM Lead"):
	"""
	Create FCRM Note linked to CRM Lead or Deal
	"""
	note = frappe.new_doc('FCRM Note')
	note.update({
		'title': title,
		'content': notes_html,
		'reference_doctype': ref_doctype,
		'reference_docname': lead_name
	})
	note.flags.ignore_permissions = True
	note.insert()
	return note.name


def make_erpnext_lead_from_inidamart(lead_values,indiamart_lead_name=None):
	try:
		output=None
		user=frappe.db.get_single_value('Indiamart Settings', 'default_lead_owner')
		country=frappe.get_value("Country", {"code": lead_values.get("SENDER_COUNTRY_ISO", "IN").lower()}) or 'India'
		state=lead_values.get('SENDER_STATE',None)
		city=lead_values.get('SENDER_CITY',None)
		email_id=lead_values.get('SENDER_EMAIL',None)
		mobile_no=lead_values.get('SENDER_MOBILE',None)		

		print("--- PROCESSING LEAD ---")
		print("Query ID:", lead_values.get('UNIQUE_QUERY_ID'))
		print("Sender:", lead_values.get('SENDER_NAME'))
		print("Mobile:", mobile_no)
		print("Email:", email_id)
		print("-----------------------")

		lead_owner=user
		lead_name = None
		lead_name = frappe.db.get_value("CRM Lead", {"query_id_cf": lead_values.get('UNIQUE_QUERY_ID')})
		# It is a new lead from indiamart
		if not lead_name :
			check_duplicate_mobile_no=mobile_no
			lead_name = frappe.db.get_value("CRM Lead", {"mobile_no": check_duplicate_mobile_no})
			#  It is a repeat user having same mobile_no
			if lead_name:
				existing_lead_output=update_existing_lead(lead_name,lead_values)
				output='Duplicate Mobile No: {0}'.format(existing_lead_output)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')			
				return output
			# It is may be a fresh lead 
			elif not lead_name:
					if email_id and email_id!='':
						lead_name = frappe.db.get_value("CRM Lead", {"email": email_id})
					# It is a repeat user having same email id
					if lead_name:
						existing_lead_output=update_existing_lead(lead_name,lead_values)
						output='Duplicate Email ID: {0}'.format(existing_lead_output)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')					
						return output
					elif not lead_name:
					# it is finally a fresh lead
						# source logic 
						source=''
						if lead_values.get('QUERY_TYPE') == 'W' :
							source= frappe.db.get_single_value('Indiamart Settings', 'direct_lead_source')
						elif lead_values.get('QUERY_TYPE') == 'B' :
							source= frappe.db.get_single_value('Indiamart Settings', 'buy_lead_source')
						elif lead_values.get('QUERY_TYPE') == 'P' :
							source= frappe.db.get_single_value('Indiamart Settings', 'call_lead_source')
						
						if source and not frappe.db.exists('CRM Lead Source', source):
							source = ''
						
						company_name=None
						if lead_values.get('SENDER_COMPANY'):
							company_name=lead_values.get('SENDER_COMPANY')
						
						notes_html="<div>Product Name :{0}</div><div>Category :{1}</div><div>Subject :{2}</div><div>Message :{3}</div><div>Lead Date :{4}</div><div>Alternate EmailID :{5}</div><div>Alternate Mobile :{6}</div><div>India Mart Query ID :{7}</div>" \
						.format( \
										frappe.bold(lead_values.get('QUERY_PRODUCT_NAME','Not specified')),
										frappe.bold(lead_values.get('QUERY_MCAT_NAME','Not specified')),
										frappe.bold(lead_values.get('SUBJECT','Not specified')),
										frappe.bold(lead_values.get('QUERY_MESSAGE','Not specified')),
										frappe.bold(lead_values.get('QUERY_TIME','Not specified')),
										frappe.bold(lead_values.get('EMAIL_ALT','Not specified')),
										frappe.bold(lead_values.get('MOBILE_ALT','Not specified')),
										frappe.bold(lead_values.get('UNIQUE_QUERY_ID','Not specified'))
										)
						
						# Extract Quantity from Message if not provided directly
						import re
						extracted_qty = lead_values.get('QUANTITY')
						if not extracted_qty and lead_values.get('QUERY_MESSAGE'):
							# Look for "Quantity : <value>" pattern
							qty_match = re.search(r'Quantity\s*:\s*([^<]+)', lead_values.get('QUERY_MESSAGE'), re.IGNORECASE)
							if qty_match:
								extracted_qty = qty_match.group(1).strip()

						address=lead_values.get('SENDER_ADDRESS')

						lead=frappe.new_doc('CRM Lead')
						lead_value_dict={
							"first_name": lead_values.get('SENDER_NAME'),
							"email":email_id,
							"mobile_no": mobile_no,
							"source":source or '',
							"organization":company_name,
							"query_id_cf":lead_values.get('UNIQUE_QUERY_ID'),
							"indiamart_product": lead_values.get('QUERY_PRODUCT_NAME'),
							"indiamart_subject": lead_values.get('SUBJECT'),
							"indiamart_category": lead_values.get('QUERY_MCAT_NAME'),
							"indiamart_quantity": extracted_qty,
							"indiamart_city": lead_values.get('SENDER_CITY'),
							"indiamart_state": lead_values.get('SENDER_STATE'),
							"indiamart_state": lead_values.get('SENDER_STATE'),
							"indiamart_message": (lead_values.get('QUERY_MESSAGE') or "").replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n"),
							'lead_owner':lead_owner,
							'status': 'New'
						}
						lead.update(lead_value_dict)
						lead.flags.ignore_mandatory = True
						lead.flags.ignore_permissions = True
						lead.insert()
						
						create_crm_note(lead.name, notes_html, "New IndiaMART Inquiry")
						
						if address:
							address_html = "<div><b>Address:</b></div><div>{0}</div>".format(address)
							address_html += "<div>City: {0}</div><div>State: {1}</div>".format(city or '', state or '')
							address_html += "<div>Country: {0}</div>".format(country or '')
							create_crm_note(lead.name, address_html, "Address Information")
						
						# update details to indiamart lead doctype
						output='CRM Lead {0} is created.'.format(lead.name)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')					
						return output
				
		else:
				# indiamart has send lead with same query id. Almost impossilble
				output='Duplicate Query_ID. It is in existing Lead {0}'.format(lead_name)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')			
				return output
	except Exception as e:
		title=_('Indiamart Error')
		seperator = "--" * 50
		error = "\n".join([format_datetime(now_datetime(),'d-MMM-y  HH:mm:ss'), "make_erpnext_lead_from_inidamart","indiamart_lead_name  "+indiamart_lead_name,str(sys.exc_info()[1]), seperator,frappe.get_traceback()])
		frappe.log_error(message=error, title=title)

def update_existing_lead(lead_name,lead_values):
		existing_lead_output=None
		lead_status = frappe.db.get_value('CRM Lead', lead_name, 'status')

		# Create a deal if the lead is already being processed (Nurture, Qualified)
		if lead_status not in ['Nurture', 'Qualified', 'Converted']:
			notes_html="<div>Product Name :{0}</div><div>Category :{1}</div><div>Subject :{2}</div><div>Message :{3}</div><div>Lead Date :{4}</div><div>Alternate EmailID :{5}</div><div>Alternate Mobile :{6}</div><div>India Mart Query ID :{7}</div>" \
			.format( \
								frappe.bold(lead_values.get('QUERY_PRODUCT_NAME','Not specified')),
								frappe.bold(lead_values.get('QUERY_MCAT_NAME','Not specified')),
								frappe.bold(lead_values.get('SUBJECT','Not specified')),
								frappe.bold(lead_values.get('QUERY_MESSAGE','Not specified')),
								frappe.bold(lead_values.get('QUERY_TIME','Not specified')),
								frappe.bold(lead_values.get('EMAIL_ALT','Not specified')),
								frappe.bold(lead_values.get('MOBILE_ALT','Not specified')),
								frappe.bold(lead_values.get('UNIQUE_QUERY_ID','Not specified'))
								)

			lead=frappe.get_doc('CRM Lead', lead_name)
			# lead.reload()
			create_crm_note(lead.name, notes_html, "New IndiaMART Inquiry")
			
			# Extract Quantity from Message for existing lead logic
			extracted_qty = lead_values.get('QUANTITY') or extract_quantity_from_message(lead_values.get('QUERY_MESSAGE'))


			lead.query_id_cf=lead_values.get('UNIQUE_QUERY_ID')
			lead.indiamart_product = lead_values.get('QUERY_PRODUCT_NAME')
			lead.indiamart_subject = lead_values.get('SUBJECT')
			lead.indiamart_category = lead_values.get('QUERY_MCAT_NAME')
			lead.indiamart_quantity = extracted_qty
			lead.indiamart_city = lead_values.get('SENDER_CITY')
			lead.indiamart_state = lead_values.get('SENDER_STATE')
			lead.indiamart_message = (lead_values.get('QUERY_MESSAGE') or "").replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
			# Update status to a valid one from CRM
			if frappe.db.exists('CRM Lead Status', 'Contacted'):
				lead.status='Contacted'
			lead.flags.ignore_mandatory = True
			lead.flags.ignore_permissions = True
			lead.save()	
			
			existing_lead_output='Lead notes updated for {0}'.format(lead_name)
			return existing_lead_output	
		else:
			to_discuss_html="Product Name : {0} \n Category : {1} \n Subject :{2} \n Message :{3} \n Lead Date :{4} \n Alternate EmailID :{5} \n Alternate Mobile :{6} \n India Mart Query ID :{7}" \
			.format( \
								frappe.bold(lead_values.get('QUERY_PRODUCT_NAME','Not specified')),
								frappe.bold(lead_values.get('QUERY_MCAT_NAME','Not specified')),
								frappe.bold(lead_values.get('SUBJECT','Not specified')),
								frappe.bold(lead_values.get('QUERY_MESSAGE','Not specified')),
								frappe.bold(lead_values.get('QUERY_TIME','Not specified')),
								frappe.bold(lead_values.get('EMAIL_ALT','Not specified')),
								frappe.bold(lead_values.get('MOBILE_ALT','Not specified')),
								frappe.bold(lead_values.get('UNIQUE_QUERY_ID','Not specified'))
								)

			from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal
			lead_doc = frappe.get_doc('CRM Lead', lead_name)
			lead_doc.flags.ignore_permissions = True
			deal_name = convert_to_deal(lead=lead_name, doc=lead_doc)
			deal = frappe.get_doc("CRM Deal", deal_name)
			deal.flags.ignore_mandatory = True
			deal.flags.ignore_permissions = True
			status = frappe.db.get_single_value('Indiamart Settings', 'default_opportunity_sales_stage')
			if status:
				deal.status = status
			deal.save()			
			
			create_crm_note(deal.name, to_discuss_html, "New IndiaMART Inquiry", "CRM Deal")

			opportunity_html='<br><br><div><B>New Deal {0} was created</B>'.format(deal.name)
			create_crm_note(lead_name, opportunity_html, "New Deal Created", "CRM Lead")

			lead=frappe.get_doc('CRM Lead', lead_name)
			# lead.reload()
			lead.query_id_cf=lead_values.get('UNIQUE_QUERY_ID')
			lead.flags.ignore_mandatory = True
			lead.flags.ignore_permissions = True
			lead.save()		
			existing_lead_output='Deal {0} created for Lead {1}'.format(deal.name,lead_name)
			return existing_lead_output						



def get_integration_request_dashboard_data(data):
	if len(data.get("transactions"))>0:
		for d in data.get("transactions",[]):
			d.update({"items":d.get("items") +["ToDo"]})
	else:
		data.get("transactions").append({"items":["ToDo"]})
	return data
