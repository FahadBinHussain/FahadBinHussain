import requests
import os

# Configuration
STATUSPAGE_API_KEY = os.getenv('STATUSPAGE_API_KEY')
PAGE_ID = os.getenv('PAGE_ID')
COMPONENT_ID = os.getenv('COMPONENT_ID')
WAKAPI_URL = 'https://wakapi.dev/api/health'
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

def check_service_status():
    if TEST_MODE:
        return 'major_outage', 'Simulated outage for testing.'
    
    try:
        response = requests.get(WAKAPI_URL)
        if response.status_code == 200:
            return 'operational', 'Wakapi is operational.'
        else:
            return 'major_outage', 'Wakapi is down.'
    except requests.exceptions.RequestException:
        return 'major_outage', 'Wakapi is down.'

def update_statuspage(component_status, incident_body):
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
            'name': 'Wakapi Service Status',
            'status': 'investigating' if component_status == 'major_outage' else 'resolved',
            'body': incident_body,
            'components': [{
                'id': COMPONENT_ID,
                'status': component_status
            }]
        }
    }

    # Update component status
    component_response = requests.patch(
        f'https://api.statuspage.io/v1/pages/{PAGE_ID}/components/{COMPONENT_ID}',
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
        print('StatusPage updated successfully')
    else:
        print('Failed to update StatusPage', component_response.content, incident_response.content)

if __name__ == '__main__':
    component_status, incident_body = check_service_status()
    update_statuspage(component_status, incident_body)