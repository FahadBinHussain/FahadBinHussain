import requests
import re
import base64
from datetime import datetime
import sys
import os

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

def fetch_most_recent_projects():
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
        
        # Remove duplicates while preserving order
        seen = set()
        unique_projects = [x for x in projects if not (x in seen or seen.add(x))]

        if unique_projects:
            # Get the two most recent projects
            most_recent_projects = unique_projects[:2]
            print(f"Most recent projects: {most_recent_projects}")
            return most_recent_projects
        else:
            print("No projects found in heartbeats.")
            return None
    else:
        print("No heartbeats found or heartbeats list is invalid.")
        return None

def update_readme(most_recent_projects):
    if not most_recent_projects or len(most_recent_projects) < 2:
        print("Less than two recent projects found to update README.")
        return

    readme_path = 'README.md'

    # Check if README.md file exists
    if not os.path.isfile(readme_path):
        print("README.md file not found.")
        return

    try:
        with open(readme_path, 'r', encoding='utf-8') as file:
            readme_content = file.read()
        print("Successfully read README.md")
    except Exception as e:
        print(f"Error reading README.md: {e}")
        return

    # Define the line to be updated
    line_to_update = re.compile(r"- 🔭 Currently actively developing my .* projects\.")
    
    # New projects section content
    new_projects_text = f"- 🔭 Currently actively developing my [{most_recent_projects[0]}](https://github.com/FahadBinHussain/{most_recent_projects[0]}) & [{most_recent_projects[1]}](https://github.com/FahadBinHussain/{most_recent_projects[1]}) projects."

    # Replace the line matching the pattern with the new content
    if line_to_update.search(readme_content):
        updated_readme_content = line_to_update.sub(new_projects_text, readme_content)
    else:
        print("Pattern not found in README.md, adding new project text.")
        updated_readme_content = readme_content + "\n" + new_projects_text

    try:
        with open(readme_path, 'w', encoding='utf-8') as file:
            file.write(updated_readme_content)
        print("Successfully updated README.md")
    except Exception as e:
        print(f"Error writing README.md: {e}")

if __name__ == "__main__":
    most_recent_projects = fetch_most_recent_projects()
    update_readme(most_recent_projects)