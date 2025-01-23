import requests
import os
import json

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
        print('StatusPage updated successfully for component:', component_id)
    else:
        print('Failed to update StatusPage for component:', component_id, component_response.content, incident_response.content)

if __name__ == '__main__':
    for service in config['services']:
        url = service['url']
        component_id = service['component_id']
        component_status, incident_body = check_service_status(url)
        update_statuspage(component_id, component_status, incident_body)