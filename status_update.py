from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import requests
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
with open('services_config.json', 'r') as config_file:
    config = json.load(config_file)

STATUSPAGE_API_KEY = os.getenv('STATUSPAGE_API_KEY')
PAGE_ID = os.getenv('PAGE_ID')
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# Add environment validation at startup
if not TEST_MODE and (not STATUSPAGE_API_KEY or not PAGE_ID):
    logging.error('Missing required environment variables:')
    logging.error('STATUSPAGE_API_KEY: %s', 'Set' if STATUSPAGE_API_KEY else 'Not set')
    logging.error('PAGE_ID: %s', 'Set' if PAGE_ID else 'Not set')
    logging.error('Exiting due to missing credentials')
    exit(1)

def check_wakapi_service_status(url):
    if TEST_MODE:
        return {'app': 'major_outage', 'db': 'major_outage'}, f'Simulated outage for testing {url}.'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            response_body = response.text.strip()
            status_parts = response_body.split("\n")
            status_dict = {part.split('=')[0]: part.split('=')[1] for part in status_parts}
            component_statuses = {}
            for component, status in status_dict.items():
                if status == '1':
                    component_statuses[component] = 'operational'
                else:
                    component_statuses[component] = 'major_outage'
            logging.info('Service status for %s: %s', url, component_statuses)
            return component_statuses, f'{url} health check completed with components status.'
        else:
            logging.info('Service status for %s: major_outage', url)
            return {'app': 'major_outage', 'db': 'major_outage'}, f'{url} is down.'
    except requests.exceptions.RequestException:
        logging.info('Service status for %s: major_outage', url)
        return {'app': 'major_outage', 'db': 'major_outage'}, f'{url} is down.'

def check_general_service_status(url):
    if TEST_MODE:
        logging.info('Test mode status for %s: major_outage', url)
        return 'major_outage', f'Simulated outage for testing {url}.'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logging.info('Service status for %s: operational', url)
            return 'operational', f'{url} is operational.'
        else:
            logging.info('Service status for %s: major_outage', url)
            return 'major_outage', f'{url} is down.'
    except requests.exceptions.RequestException:
        logging.info('Service status for %s: major_outage', url)
        return 'major_outage', f'{url} is down.'

def get_component_status(component_id):
    if not STATUSPAGE_API_KEY or not PAGE_ID:
        logging.error('Missing Statuspage credentials - API_KEY: %s, PAGE_ID: %s', 
                     bool(STATUSPAGE_API_KEY), bool(PAGE_ID))
        return None

    headers = {
        'Authorization': f'OAuth {STATUSPAGE_API_KEY}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/components/{component_id}',
            headers=headers,
            timeout=10
        )

        if response.status_code == 401:
            logging.error('Authentication failed - invalid API key or page ID')
            return None

        if response.status_code == 200:
            component = response.json()
            return component['status']
        else:
            logging.error('Failed to fetch component status: %s', response.content)
            return None
    except requests.exceptions.RequestException as e:
        logging.error('Network error fetching component status: %s', str(e))
        return None

def update_statuspage(component_id, component_status, incident_body):
    if not STATUSPAGE_API_KEY or not PAGE_ID:
        logging.error('Skipping update - missing Statuspage credentials')
        return

    headers = {
        'Authorization': f'OAuth {STATUSPAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    component_update = {
        'component': {
            'status': component_status
        }
    }
    incident_update = {
        'incident': {
            'name': 'Service Status',
            'status': 'investigating' if component_status == 'major_outage' else 'resolved',
            'body': incident_body,
            'components': [{
                'id': component_id,
                'status': component_status
            }]
        }
    }

    try:
        # Update component status
        component_response = requests.patch(
            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/components/{component_id}',
            headers=headers,
            json=component_update,
            timeout=15
        )

        if component_response.status_code == 401:
            logging.error('Authentication failed during component update')
            return

        # Create or update incident
        incident_response = requests.post(
            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents',
            headers=headers,
            json=incident_update
        )

        if component_response.status_code == 200 and incident_response.status_code in [200, 201]:
            logging.info('StatusPage updated successfully for component: %s', component_id)
        else:
            logging.error('Failed to update StatusPage for component: %s - %s - %s', component_id, component_response.content, incident_response.content)
    except Exception as e:
        logging.error('Error updating StatusPage for component: %s - %s', component_id, str(e))

def resolve_incident(incident_id):
    headers = {
        'Authorization': f'OAuth {STATUSPAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    incident_update = {
        'incident': {
            'status': 'resolved',
            'body': 'The issue has been resolved.'
        }
    }

    response = requests.patch(
        f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents/{incident_id}',
        headers=headers,
        json=incident_update
    )

    if response.status_code == 200:
        logging.info('Incident resolved successfully')
    else:
        logging.error('Failed to resolve incident: %s', response.content)

if __name__ == '__main__':
    outage_detected = False
    for service in config['services']:
        url = service['url']
        if 'components' in service:
            for component in service['components']:
                component_statuses, _ = check_wakapi_service_status(url)
                if any(status != 'operational' for status in component_statuses.values()):
                    outage_detected = True
        else:
            status, _ = check_general_service_status(url)
            if status != 'operational':
                outage_detected = True

    if outage_detected:
        logging.error('Outage detected - failing workflow to trigger notifications')
        exit(1)
    else:
        logging.info('All services operational')
        exit(0)