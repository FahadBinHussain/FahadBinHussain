import os
import re
from collections import Counter
from typing import Iterable

import requests
from dotenv import load_dotenv

load_dotenv()

README_MARKER_START = "<!--START_SECTION:stack-->"
README_MARKER_END = "<!--END_SECTION:stack-->"
GITHUB_API_URL = "https://api.github.com"


BADGE_MAP = {
    "JavaScript": ("JavaScript", "javascript", "F7DF1E", "323330"),
    "TypeScript": ("TypeScript", "typescript", "white", "3178C6"),
    "Python": ("Python", "python", "ffdd54", "3670A0"),
    "Java": ("Java", "openjdk", "white", "ED8B00"),
    "HTML": ("HTML5", "html5", "white", "E34F26"),
    "CSS": ("CSS3", "css3", "white", "1572B6"),
    "Shell": ("Shell", "gnubash", "white", "121011"),
    "C++": ("C++", "cplusplus", "white", "00599C"),
    "C": ("C", "c", "white", "A8B9CC"),
    "Docker": ("Docker", "docker", "white", "2496ED"),
    "Flask": ("Flask", "flask", "white", "000000"),
    "Django": ("Django", "django", "white", "092E20"),
    "Node.js": ("Node.js", "node.js", "white", "339933"),
    "React": ("React", "react", "61DAFB", "20232A"),
    "Next.js": ("Next.js", "nextdotjs", "white", "000000"),
    "Vue": ("Vue", "vuedotjs", "white", "4FC08D"),
    "Svelte": ("Svelte", "svelte", "white", "FF3E00"),
    "Express": ("Express", "express", "white", "000000"),
    "Prisma": ("Prisma", "prisma", "white", "2D3748"),
    "MongoDB": ("MongoDB", "mongodb", "white", "47A248"),
    "PostgreSQL": ("PostgreSQL", "postgresql", "white", "4169E1"),
    "MySQL": ("MySQL", "mysql", "white", "4479A1"),
    "SQLite": ("SQLite", "sqlite", "white", "003B57"),
    "Redis": ("Redis", "redis", "white", "DC382D"),
    "Firebase": ("Firebase", "firebase", "black", "FFCA28"),
    "Selenium": ("Selenium", "selenium", "white", "43B02A"),
    "Puppeteer": ("Puppeteer", "puppeteer", "white", "40B5A4"),
    "Playwright": ("Playwright", "playwright", "white", "2EAD33"),
    "GitHub Actions": ("GitHub Actions", "githubactions", "white", "2088FF"),
    "Git": ("Git", "git", "white", "F05032"),
    "Linux": ("Linux", "linux", "white", "000000"),
    "PowerShell": ("PowerShell", "powershell", "white", "5391FE"),
    "Google Cloud": ("Google Cloud", "googlecloud", "white", "4285F4"),
    "Docker Compose": ("Docker Compose", "docker", "white", "2496ED"),
}


FILE_HINTS = {
    "package.json": {"Node.js"},
    "package-lock.json": {"Node.js"},
    "pnpm-lock.yaml": {"Node.js"},
    "yarn.lock": {"Node.js"},
    "requirements.txt": {"Python"},
    "pyproject.toml": {"Python"},
    "Pipfile": {"Python"},
    "pom.xml": {"Java"},
    "build.gradle": {"Java"},
    "build.gradle.kts": {"Java"},
    "Dockerfile": {"Docker"},
    "docker-compose.yml": {"Docker Compose", "Docker"},
    "docker-compose.yaml": {"Docker Compose", "Docker"},
    ".github/workflows": {"GitHub Actions"},
    "next.config.js": {"Next.js", "React", "Node.js"},
    "next.config.mjs": {"Next.js", "React", "Node.js"},
    "next.config.ts": {"Next.js", "React", "Node.js"},
    "vite.config.js": {"Node.js"},
    "vite.config.ts": {"Node.js"},
    "manage.py": {"Django", "Python"},
    "wsgi.py": {"Django", "Python"},
    "flask_app.py": {"Flask", "Python"},
}


CONTENT_HINTS = {
    "react": {"React"},
    "next": {"Next.js", "React"},
    "express": {"Express"},
    "prisma": {"Prisma"},
    "mongoose": {"MongoDB"},
    "mongodb": {"MongoDB"},
    "postgres": {"PostgreSQL"},
    "mysql": {"MySQL"},
    "sqlite": {"SQLite"},
    "redis": {"Redis"},
    "firebase": {"Firebase"},
    "selenium": {"Selenium"},
    "puppeteer": {"Puppeteer"},
    "playwright": {"Playwright"},
    "google-cloud": {"Google Cloud"},
    "@google-cloud": {"Google Cloud"},
}


def build_headers() -> dict[str, str]:
    token = (
        os.getenv("GITHUB_TOKEN")
        or os.getenv("PAT_1")
        or os.getenv("GITHUB_TOKEN1")
        or os.getenv("METRICS_TOKEN")
    )
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_json(url: str, headers: dict[str, str], params: dict | None = None):
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_repositories(username: str, headers: dict[str, str], max_repos: int = 30) -> list[dict]:
    repos = fetch_json(
        f"{GITHUB_API_URL}/users/{username}/repos",
        headers,
        params={"per_page": max_repos, "sort": "updated", "type": "owner"},
    )
    return [repo for repo in repos if not repo.get("fork")]


def fetch_languages(repo: dict, headers: dict[str, str]) -> Counter:
    data = fetch_json(repo["languages_url"], headers)
    return Counter(data)


def fetch_repo_tree(repo: dict, headers: dict[str, str]) -> list[str]:
    branch = repo.get("default_branch", "main")
    tree = fetch_json(
        f"{GITHUB_API_URL}/repos/{repo['full_name']}/git/trees/{branch}",
        headers,
        params={"recursive": "1"},
    )
    return [item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"]


def fetch_file_content(repo: dict, headers: dict[str, str], path: str) -> str:
    data = fetch_json(f"{GITHUB_API_URL}/repos/{repo['full_name']}/contents/{path}", headers)
    if data.get("encoding") != "base64" or "content" not in data:
        return ""
    import base64

    return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")


def detect_tools_from_paths(paths: Iterable[str]) -> set[str]:
    detected: set[str] = set()
    path_set = set(paths)
    for hint_path, tools in FILE_HINTS.items():
        if hint_path in path_set or any(path.startswith(f"{hint_path}/") for path in path_set):
            detected.update(tools)
    return detected


def detect_tools_from_content(content: str) -> set[str]:
    detected: set[str] = set()
    lowered = content.lower()
    for needle, tools in CONTENT_HINTS.items():
        if needle in lowered:
            detected.update(tools)
    return detected


def normalize_language_name(name: str) -> str | None:
    mapping = {
        "Jupyter Notebook": "Python",
        "Vue": "Vue",
        "HTML": "HTML",
        "CSS": "CSS",
        "JavaScript": "JavaScript",
        "TypeScript": "TypeScript",
        "Python": "Python",
        "Java": "Java",
        "Shell": "Shell",
        "C++": "C++",
        "C": "C",
    }
    return mapping.get(name)


def gather_stack(username: str, max_repos: int = 20) -> tuple[list[str], list[str]]:
    headers = build_headers()
    repos = fetch_repositories(username, headers, max_repos=max_repos)
    language_counts: Counter = Counter()
    tool_counts: Counter = Counter()

    for repo in repos:
        language_counts.update(fetch_languages(repo, headers))

        try:
            paths = fetch_repo_tree(repo, headers)
        except requests.RequestException:
            paths = []

        detected_tools = detect_tools_from_paths(paths)

        for candidate in ("package.json", "requirements.txt", "pyproject.toml", "pom.xml"):
            if candidate in paths:
                try:
                    detected_tools.update(detect_tools_from_content(fetch_file_content(repo, headers, candidate)))
                except requests.RequestException:
                    continue

        for tool in detected_tools:
            tool_counts[tool] += 1

    languages = [
        name
        for name, _ in language_counts.most_common()
        if normalize_language_name(name) in BADGE_MAP
    ]
    normalized_languages = []
    seen_languages = set()
    for language in languages:
        normalized = normalize_language_name(language)
        if normalized and normalized not in seen_languages:
            normalized_languages.append(normalized)
            seen_languages.add(normalized)

    tools = [name for name, _ in tool_counts.most_common() if name in BADGE_MAP and name not in seen_languages]
    return normalized_languages[:8], tools[:12]


def badge_markdown(name: str) -> str:
    label, logo, logo_color, color = BADGE_MAP[name]
    return (
        f"![{label}](https://img.shields.io/badge/{label.replace(' ', '%20')}-{color}"
        f"?style=for-the-badge&logo={logo}&logoColor={logo_color})"
    )


def build_stack_block(languages: list[str], tools: list[str]) -> str:
    parts = ["", README_MARKER_START, ""]
    if languages:
        parts.append("**Languages**")
        parts.append("")
        parts.append(" ".join(badge_markdown(language) for language in languages))
        parts.append("")
    if tools:
        parts.append("**Tools & Frameworks**")
        parts.append("")
        parts.append(" ".join(badge_markdown(tool) for tool in tools))
        parts.append("")
    parts.append(README_MARKER_END)
    return "\n".join(parts)


def replace_stack_block(readme_content: str, new_block: str) -> str:
    pattern = re.compile(
        rf"{re.escape(README_MARKER_START)}.*?{re.escape(README_MARKER_END)}",
        re.DOTALL,
    )
    if pattern.search(readme_content):
        return pattern.sub(new_block.strip(), readme_content)
    return readme_content


def update_readme_stack(readme_path: str = "README.md", username: str | None = None) -> None:
    username = username or os.getenv("GITHUB_USERNAME") or "FahadBinHussain"
    languages, tools = gather_stack(username)
    new_block = build_stack_block(languages, tools)

    with open(readme_path, "r", encoding="utf-8") as file:
        readme_content = file.read()

    updated_content = replace_stack_block(readme_content, new_block)

    with open(readme_path, "w", encoding="utf-8") as file:
        file.write(updated_content)


if __name__ == "__main__":
    update_readme_stack()
