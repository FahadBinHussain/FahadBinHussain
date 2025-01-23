import requests
import os
import re

WAKATIME_API_KEY = os.getenv('WAKATIME_API_KEY')
API_BASE_URL = "https://wakapi-qt1b.onrender.com/api/v1/users/current/projects"

headers = {
    'Authorization': f'Bearer {WAKATIME_API_KEY}'
}

def fetch_top_projects():
    response = requests.get(API_BASE_URL, headers=headers)
    projects = response.json().get('data', [])
    # Sort projects by total time spent
    projects.sort(key=lambda x: x['total_seconds'], reverse=True)
    # Get top 2 projects
    top_projects = projects[:2]
    return top_projects

def update_readme(top_projects):
    with open('README.md', 'r') as file:
        readme_content = file.read()

    # New projects section content
    new_projects_text = f"- 🔭 Currently actively developing my {top_projects[0]['name']} & {top_projects[1]['name']} projects."

    # Define a regex pattern to find the line to be replaced
    pattern = re.compile(r"- 🔭 Currently actively developing my .*projects\.")

    # Replace the line matching the pattern with the new content
    updated_readme_content = re.sub(pattern, new_projects_text, readme_content)

    with open('README.md', 'w') as file:
        file.write(updated_readme_content)

if __name__ == "__main__":
    top_projects = fetch_top_projects()
    update_readme(top_projects)