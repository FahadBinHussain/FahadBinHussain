import requests
import re
import base64
from datetime import datetime
import sys

# Set the default encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

# Directly set the WAKATIME_API_KEY and USERNAME for testing purposes
WAKATIME_API_KEY = "853c1504-3a07-4ff9-94fb-6cce94b1dd9d"
WAKATIME_USERNAME = "fahad"

if WAKATIME_API_KEY is None or WAKATIME_USERNAME is None:
    raise ValueError("WAKATIME_API_KEY and WAKATIME_USERNAME environment variables must be set")

# Encode the API key as Base64 and prefix with 'Basic '
encoded_api_key = base64.b64encode(WAKATIME_API_KEY.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_api_key}'
}

# API base URL for fetching heartbeats
HEARTBEATS_API_URL = f"https://wakapi-qt1b.onrender.com/api/compat/wakatime/v1/users/{WAKATIME_USERNAME}/heartbeats"

def fetch_most_recent_project():
    # Get the current date in YYYY-MM-DD format
    current_date = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(HEARTBEATS_API_URL, headers=headers, params={'date': current_date})
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.content.decode('utf-8')}")

    try:
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        heartbeats = data.get('data', [])
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        return None
    except ValueError as json_err:
        print(f"JSON decode error: {json_err}")
        return None

    # Check if heartbeats data is a list and not empty
    if isinstance(heartbeats, list) and heartbeats:
        # Print the fetched heartbeats for debugging
        print(f"Fetched heartbeats: {heartbeats}")

        # Extract project names from heartbeats
        projects = [hb['project'] for hb in heartbeats if 'project' in hb and hb['project']]
        
        if projects:
            # Get the most recent project (assuming the list is sorted by time)
            most_recent_project = projects[0]
            print(f"Most recent project: {most_recent_project}")
            return most_recent_project
        else:
            print("No projects found in heartbeats.")
            return None
    else:
        print("No heartbeats found or heartbeats list is invalid.")
        return None

def update_readme(most_recent_project):
    if not most_recent_project:
        print("No recent project found to update README.")
        return

    try:
        with open('README.md', 'r', encoding='utf-8') as file:
            readme_content = file.read()
    except FileNotFoundError:
        print("README.md file not found.")
        return

    # New projects section content
    new_projects_text = f"- 🔭 Currently actively developing my {most_recent_project} project."
    print(f"New projects text: {new_projects_text}")

    # Define a regex pattern to find the line to be replaced
    pattern = re.compile(r"- 🔭 Currently actively developing my .*project\.")

    # Replace the line matching the pattern with the new content
    updated_readme_content = re.sub(pattern, new_projects_text, readme_content)

    with open('README.md', 'w', encoding='utf-8') as file:
        file.write(updated_readme_content)
    print("README.md has been updated.")

if __name__ == "__main__":
    most_recent_project = fetch_most_recent_project()
    update_readme(most_recent_project)