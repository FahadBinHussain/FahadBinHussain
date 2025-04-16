from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import requests
import os
import json
import logging
import time
import random

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

def is_render_service(url):
    """Check if the URL is for a service hosted on Render"""
    return 'onrender.com' in url.lower()

def get_service_specific_timeout(url, service_name=None):
    """Get service-specific timeout values based on the URL or service name"""
    base_timeout = 5  # Default base timeout
    max_timeout = 15  # Default max timeout
    
    # Special case for Wakapi which seems to have longer cold starts
    if 'wakapi' in url.lower():
        base_timeout = 30  # Much longer initial timeout for Wakapi
        max_timeout = 45  # Higher maximum timeout
    # General case for all Render services
    elif is_render_service(url):
        base_timeout = 15  # Longer initial timeout for Render services
        max_timeout = 30  # Higher maximum timeout
    
    return base_timeout, max_timeout

def check_general_service_status(url):
    if TEST_MODE:
        logging.info('Test mode status for %s: major_outage', url)
        return 'major_outage', f'Simulated outage for testing {url}.'
    
    # Get service-specific timeout values
    base_timeout, max_timeout = get_service_specific_timeout(url)
    
    # Progressive timeout strategy - start with service-specific timeout and increase on retries
    timeout = base_timeout
    retry_attempts = 2  # Number of retry attempts
    
    for attempt in range(retry_attempts + 1):
        try:
            logging.info(f"Attempt {attempt+1}/{retry_attempts+1} for {url} with timeout={timeout}s")
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                logging.info('Service status for %s: operational', url)
                return 'operational', f'{url} is operational.'
            else:
                # Only return error on the last attempt
                if attempt == retry_attempts:
                    logging.warning('Service status for %s: HTTP %s - major_outage', url, response.status_code)
                    return 'major_outage', f'{url} returned HTTP {response.status_code}.'
        except requests.exceptions.RequestException as e:
            # Only return error on the last attempt
            if attempt == retry_attempts:
                logging.warning('Service status for %s: Connection error - %s', url, str(e))
                return 'major_outage', f'{url} connection error: {str(e)}.'
        
        # Increase timeout for next attempt if we're retrying
        if attempt < retry_attempts:
            timeout = min(timeout * 1.5, max_timeout)  # Increase timeout by 50% for next attempt
            time.sleep(random.uniform(0.5, 1.0))  # Add a small delay between attempts

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
    
    try:
        # First, update component status
        component_response = requests.patch(
            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/components/{component_id}',
            headers=headers,
            json=component_update,
            timeout=15
        )

        if component_response.status_code == 401:
            logging.error('Authentication failed during component update')
            return
        elif component_response.status_code != 200:
            logging.error('Failed to update component status: %s - %s', component_id, component_response.content)
            return

        # Get unresolved incidents
        incidents_response = requests.get(
            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents/unresolved',
            headers=headers,
            timeout=15
        )
        
        if incidents_response.status_code == 200:
            incidents = incidents_response.json()
            existing_incidents = []
            
            # Look for ALL existing incidents that include this component
            # More robust checking for component association with incident
            for incident in incidents:
                # Check if component is in the incident name (since this is how we create them)
                if f"Service Issue - {component_id}" == incident.get('name'):
                    existing_incidents.append(incident)
                # Also check if component is in the components dict (backcompat)
                elif component_id in incident.get('components', {}):
                    existing_incidents.append(incident)
            
            logging.info(f"Found {len(existing_incidents)} existing unresolved incidents for component {component_id}")

            if component_status == 'operational':
                # If component is operational, resolve ALL existing incidents for this component
                if existing_incidents:
                    for existing_incident in existing_incidents:
                        incident_id = existing_incident['id']
                        resolve_response = requests.patch(
                            f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents/{incident_id}',
                            headers=headers,
                            json={
                                'incident': {
                                    'status': 'resolved',
                                    'body': 'The service has returned to operational status.'
                                }
                            },
                            timeout=15
                        )
                        
                        if resolve_response.status_code == 200:
                            logging.info('Resolved incident %s for component: %s', incident_id, component_id)
                        else:
                            logging.error('Failed to resolve incident: %s - %s', incident_id, resolve_response.content)
                
                logging.info('Component %s is operational', component_id)
            else:
                # For non-operational status, use the first incident if any exist, otherwise create new
                if existing_incidents:
                    # Update most recent existing incident
                    incident_id = existing_incidents[0]['id']
                    update_response = requests.patch(
                        f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents/{incident_id}',
                        headers=headers,
                        json={
                            'incident': {
                                'body': incident_body,
                                'status': 'investigating'
                            }
                        },
                        timeout=15
                    )
                    
                    if update_response.status_code == 200:
                        logging.info('Updated existing incident for component: %s', component_id)
                    else:
                        logging.error('Failed to update existing incident: %s - %s', incident_id, update_response.content)
                else:
                    # Create new incident
                    incident_update = {
                        'incident': {
                            'name': f'Service Issue - {component_id}',
                            'status': 'investigating',
                            'body': incident_body,
                            'component_ids': [component_id]
                        }
                    }
                    
                    incident_response = requests.post(
                        f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents',
                        headers=headers,
                        json=incident_update,
                        timeout=15
                    )
                    
                    if incident_response.status_code in [200, 201]:
                        logging.info('Created new incident for component: %s', component_id)
                    else:
                        logging.error('Failed to create incident for component: %s - %s', component_id, incident_response.content)
        else:
            logging.error('Failed to get unresolved incidents: %s', incidents_response.content)
        
        logging.info('StatusPage updated successfully for component: %s', component_id)
    except Exception as e:
        logging.error('Error updating StatusPage for component: %s - %s', component_id, str(e))

if __name__ == '__main__':
    overall_outage_detected = False # Use a clearer name

    for service in config['services']:
        url = service['url']
        # Ensure component_id exists, otherwise skip or log error
        if 'component_id' not in service:
            logging.warning(f"Skipping service {service.get('url', 'Unknown URL')} - missing 'component_id' in config.")
            continue

        component_id = service['component_id']

        # Perform the check for the service
        status, message = check_general_service_status(url)

        # Update StatusPage regardless of the result
        # Only update if not in test mode
        if not TEST_MODE:
             update_statuspage(component_id, status, message)
        else:
             logging.info(f"TEST MODE: Would update component {component_id} to {status} with message: {message}")


        # If this service is not operational, mark that an outage was detected
        if status != 'operational':
            overall_outage_detected = True

    # After checking all services, decide the exit code
    if overall_outage_detected:
        logging.error('One or more services reported an outage - failing workflow to trigger notifications')
        exit(1)
    else:
        logging.info('All services checked and operational')
        exit(0)