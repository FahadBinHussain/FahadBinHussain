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

# Set the default encoding to utf-8 where available
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    # Older Python versions or environments may not support reconfigure; ignore silently
    pass

# Encode the API key as Base64 and prefix with 'Basic ' if present
if WAKATIME_API_KEY:
    encoded_api_key = base64.b64encode(WAKATIME_API_KEY.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_api_key}'}
else:
    headers = {}

# API base URL for fetching heartbeats
HEARTBEATS_API_URL = f"https://wakapi-qt1b.onrender.com/api/compat/wakatime/v1/users/{WAKATIME_USERNAME}/heartbeats"

def fetch_most_recent_projects():
    # Get the current date in YYYY-MM-DD format
    if WAKATIME_API_KEY is None or WAKATIME_USERNAME is None:
        print("WAKATIME_API_KEY and WAKATIME_USERNAME are not set. Skipping fetch.")
        return None
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
            # Get the three most recent projects
            most_recent_projects = unique_projects[:3]
            print(f"Most recent projects: {most_recent_projects}")
            return most_recent_projects
        else:
            print("No projects found in heartbeats.")
            return None
    else:
        print("No heartbeats found or heartbeats list is invalid.")
        return None

def build_new_projects_text(most_recent_projects, max_projects=3):
    if not most_recent_projects:
        return None

    projects = most_recent_projects[:max_projects]
    links = [f"[{p}](https://github.com/FahadBinHussain/{p})" for p in projects]

    if len(links) == 1:
        return f"- 🔭 Currently actively developing my {links[0]} project."
    elif len(links) == 2:
        return f"- 🔭 Currently actively developing my {links[0]} & {links[1]} projects."
    else:
        # Join all but the last with commas, use & before the final project
        return f"- 🔭 Currently actively developing my {', '.join(links[:-1])} & {links[-1]} projects."


def replace_projects_block(readme_content: str, new_projects_text: str) -> str:
    """Replace one or more lines that start with the projects line with a single new_projects_text.

    The regex matches either 'project.' or 'projects.' and supports CRLF/LF newlines.
    """
    if not new_projects_text:
        return readme_content

    # Match one or more occurrences (possible blocks) of the projects statement lines
    # We match lines individually and include optional whitespace and CRLF/LF
    block_re = re.compile(r"^\s*- 🔭 Currently actively developing my .*?project(?:s)?\.\s*$\r?\n?", re.M)

    if block_re.search(readme_content):
        # Remove all existing occurrences (deduplicate)
        content_clean = block_re.sub('', readme_content)

        # Insert the new projects line after the first bullet that describes education (approx location)
        insert_after_re = re.compile(r"(^\s*- 🎓 .*?$\r?\n?)", re.M)
        if insert_after_re.search(content_clean):
            content_inserted = insert_after_re.sub(r"\1" + new_projects_text + "\n", content_clean, count=1)
            return content_inserted
        else:
            # fallback: append to the end
            if not content_clean.endswith("\n"):
                content_clean += "\n"
            return content_clean + new_projects_text + "\n"
    else:
        # If not found, append the projects line at the end
        if not readme_content.endswith("\n"):
            readme_content += "\n"
    # If no occurrences found, append to end as before
    return readme_content + new_projects_text + "\n"


def update_readme(most_recent_projects, readme_path='README.md'):
    if not most_recent_projects:
        print("No recent projects found to update README.")
        return

    # Allow custom readme_path for testing/invocation

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

    new_projects_text = build_new_projects_text(most_recent_projects)

    if not new_projects_text:
        print("No recent projects found to update README.")
        return

    updated_readme_content = replace_projects_block(readme_content, new_projects_text)

    try:
        with open(readme_path, 'w', encoding='utf-8') as file:
            file.write(updated_readme_content)
        print("Successfully updated README.md")
    except Exception as e:
        print(f"Error writing README.md: {e}")

if __name__ == "__main__":
    most_recent_projects = fetch_most_recent_projects()
    update_readme(most_recent_projects)
