import re
import requests

def parse_github_url(url):
    """Extract owner/repo from a GitHub URL, stripping .git suffix."""
    pattern = r'github\.com/([^/]+)/([^/]+?)(\.git)?/?$'
    match = re.search(pattern, url.strip())
    if not match:
        raise ValueError("Invalid GitHub URL")
    return match.group(1), match.group(2)

def fetch_repo_data(owner, repo):
    base = f"https://api.github.com/repos/{owner}/{repo}"
    repo_resp = requests.get(base)
    repo_resp.raise_for_status()
    repo_data = repo_resp.json()

    lang_resp = requests.get(f"{base}/languages")
    lang_data = lang_resp.json() if lang_resp.ok else {}

    return {
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "languages": lang_data,
    }