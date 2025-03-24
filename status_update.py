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

def check_multi_component_service_status(url, service_name):
    if TEST_MODE:
        default_components = {
            'wakapi': {'app': 'major_outage', 'db': 'major_outage'},
            'xenovate': {'frontend': 'major_outage', 'backend': 'major_outage'}
        }
        component_statuses = default_components.get(service_name, {'service': 'major_outage'})
        return component_statuses, f'Simulated outage for testing {url}.'
    
    # Default component names based on the service
    default_components = {
        'wakapi': ['app', 'db'],
        'xenovate': ['frontend', 'backend']
    }
    
    # Progressive timeout strategy - start with shorter timeout and increase on retries
    timeout = 5  # Start with a 5-second timeout
    max_timeout = 15  # Maximum timeout in seconds
    retry_attempts = 2  # Number of retry attempts
    
    for attempt in range(retry_attempts + 1):
        try:
            # Add a random delay between 0.1 and 0.5 seconds to prevent race conditions
            time.sleep(random.uniform(0.1, 0.5))
            
            logging.info(f"Attempt {attempt+1}/{retry_attempts+1} for {url} with timeout={timeout}s")
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                try:
                    response_body = response.text.strip()
                    status_parts = response_body.split("\n")
                    status_dict = {}
                    
                    # Parse the response more robustly
                    for part in status_parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            status_dict[key] = value
                    
                    component_statuses = {}
                    for component, status in status_dict.items():
                        if status == '1':
                            component_statuses[component] = 'operational'
                        else:
                            component_statuses[component] = 'major_outage'
                    
                    # If we couldn't parse any components, use the defaults
                    if not component_statuses:
                        components = default_components.get(service_name, ['service'])
                        component_statuses = {comp: 'operational' for comp in components}
                    
                    logging.info('Service status for %s: %s', url, component_statuses)
                    return component_statuses, f'{url} health check completed successfully.'
                except Exception as e:
                    logging.warning('Error parsing response from %s: %s. Assuming service is operational.', url, str(e))
                    components = default_components.get(service_name, ['service'])
                    component_statuses = {comp: 'operational' for comp in components}
                    return component_statuses, f'{url} appears to be operational but response format is unexpected.'
            else:
                # Only return error immediately on the last attempt
                if attempt == retry_attempts:
                    components = default_components.get(service_name, ['service'])
                    component_statuses = {comp: 'major_outage' for comp in components}
                    logging.warning('Service status for %s: HTTP %s - Setting components to major_outage', url, response.status_code)
                    return component_statuses, f'{url} returned HTTP {response.status_code}.'
        except requests.exceptions.RequestException as e:
            # Only return error immediately on the last attempt
            if attempt == retry_attempts:
                components = default_components.get(service_name, ['service'])
                component_statuses = {comp: 'major_outage' for comp in components}
                logging.warning('Service status for %s: Connection error - %s', url, str(e))
                return component_statuses, f'{url} connection error: {str(e)}.'
        
        # Increase timeout for next attempt if we're retrying
        if attempt < retry_attempts:
            timeout = min(timeout * 1.5, max_timeout)  # Increase timeout by 50% for next attempt

def check_general_service_status(url):
    if TEST_MODE:
        logging.info('Test mode status for %s: major_outage', url)
        return 'major_outage', f'Simulated outage for testing {url}.'
    
    # Progressive timeout strategy - start with shorter timeout and increase on retries
    timeout = 5  # Start with a 5-second timeout
    max_timeout = 15  # Maximum timeout in seconds
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

        # Only create incident if the component is not operational
        if component_status != 'operational':
            # Check if there's already an active incident for this component
            incidents_response = requests.get(
                f'https://api.statuspage.io/v1/pages/{PAGE_ID}/incidents/unresolved',
                headers=headers,
                timeout=15
            )
            
            if incidents_response.status_code == 200:
                incidents = incidents_response.json()
                existing_incident = None
                
                # Look for an existing incident that includes this component
                for incident in incidents:
                    incident_components = incident.get('components', {})
                    if component_id in incident_components:
                        existing_incident = incident
                        break
                
                if existing_incident:
                    # Update existing incident
                    incident_id = existing_incident['id']
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
                            'component_ids': [component_id]  # Use component_ids instead of components
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
        else:
            logging.info('Component %s is operational, no incident created', component_id)
        
        logging.info('StatusPage updated successfully for component: %s', component_id)
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

def get_service_name_from_url(url):
    """Extract service name from URL for multi-component services"""
    if 'wakapi' in url.lower():
        return 'wakapi'
    elif 'xenovate' in url.lower():
        return 'xenovate'
    else:
        return 'unknown'

def is_real_outage(status_dict):
    """Verifies if there's a real outage by checking all component statuses"""
    if not status_dict:
        return True  # If no status data, assume outage
    
    # Check if all components report an outage
    return all(status != 'operational' for status in status_dict.values())

if __name__ == '__main__':
    outage_detected = False
    max_retries = 3
    retry_delay = 2  # Longer delay between main retries
    
    for service in config['services']:
        url = service['url']
        service_outage = False
        
        if 'components' in service:
            # Handle multi-component services (wakapi, xenovate, etc.)
            service_name = get_service_name_from_url(url)
            
            # Start with a single check using our progressive timeout approach
            component_statuses, message = check_multi_component_service_status(url, service_name)
            
            # If we detected an outage with the progressive checks already implemented,
            # we don't need to do additional retries as the check function already does retries
            for component in service['components']:
                component_name = component['name']
                component_id = component['component_id']
                component_status = component_statuses.get(component_name, 'major_outage')
                
                current_status = get_component_status(component_id)
                if current_status != component_status:
                    update_statuspage(component_id, component_status, 
                                     f"{component_name} status: {component_status}. {message}")
                
                if component_status != 'operational':
                    service_outage = True
        else:
            # Handle single-component services - the check function already implements retries
            status, message = check_general_service_status(url)
            component_id = service['component_id']
            
            current_status = get_component_status(component_id)
            if current_status != status:
                update_statuspage(component_id, status, message)
            
            if status != 'operational':
                service_outage = True
        
        if service_outage:
            outage_detected = True

    if outage_detected:
        logging.error('Outage detected - failing workflow to trigger notifications')
        exit(1)
    else:
        logging.info('All services operational')
        exit(0)