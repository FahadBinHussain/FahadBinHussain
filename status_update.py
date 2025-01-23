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

def check_service_status(url):
    if TEST_MODE:
        return 'major_outage', f'Simulated outage for testing {url}.'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return 'operational', f'{url} is operational.'
        else:
            return 'major_outage', f'{url} is down.'
    except requests.exceptions.RequestException:
        return 'major_outage', f'{url} is down.'

def get_component_status(component_id):
    headers = {
        'Authorization': f'OAuth {STATUSPAGE_API_KEY}',
        'Content-Type': 'application/json'
    }

    response = requests.get(
        f'https://api.statuspage.io/v1/pages/{PAGE_ID}/components/{component_id}',
        headers=headers
    )

    if response.status_code == 200:
        component = response.json()
        return component['status']
    else:
        logging.error('Failed to fetch component status: %s', response.content)
        return None

def update_statuspage(component_id, component_status, incident_body):
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
            json=component_update
        )

        # Create or update incident
        incident_response = requests.post(
            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents',
            headers=headers,
            json=incident_update
        )

        if component_response.status_code == 200 and incident_response.status_code == 201:
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
    for service in config['services']:
        url = service['url']
        component_id = service['component_id']
        current_status = get_component_status(component_id)
        component_status, incident_body = check_service_status(url)

        if current_status != component_status:
            update_statuspage(component_id, component_status, incident_body)
        else:
            logging.info('No status change for component %s', component_id)