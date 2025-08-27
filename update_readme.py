import requests
import re
import base64
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

WAKATIME_API_KEY = os.getenv('WAKATIME_API_KEY')
WAKATIME_USERNAME = os.getenv('WAKATIME_USERNAME')

# Set the default encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

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
        print(f"API response data: {data}")  # Debug statement
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

        # Extract project names and timestamps from heartbeats
        projects_with_timestamps = [(hb['project'], hb['time']) for hb in heartbeats if 'project' in hb and hb['project']]

        # Sort projects by timestamp in descending order (most recent first)
        projects_with_timestamps.sort(key=lambda x: x[1], reverse=True)

        # Remove duplicates while preserving order
        seen = set()
        unique_projects = [x[0] for x in projects_with_timestamps if not (x[0] in seen or seen.add(x[0]))]
        print(f"Unique projects: {unique_projects}")  # Debug statement

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
    if not most_recent_projects:
        print("No recent projects found to update README.")
        return

    readme_path = 'README.md'

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

    line_to_update = re.compile(r"- 🔭 Currently actively developing my .* projects\.")

    # Build text depending on how many projects we have
    if len(most_recent_projects) >= 2:
        new_projects_text = (
            f"- 🔭 Currently actively developing my "
            f"[{most_recent_projects[0]}](https://github.com/FahadBinHussain/{most_recent_projects[0]}) "
            f"& [{most_recent_projects[1]}](https://github.com/FahadBinHussain/{most_recent_projects[1]}) projects."
        )
    else:  # only 1 project
        new_projects_text = (
            f"- 🔭 Currently actively developing my "
            f"[{most_recent_projects[0]}](https://github.com/FahadBinHussain/{most_recent_projects[0]}) project."
        )

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
