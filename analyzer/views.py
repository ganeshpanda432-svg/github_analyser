import re
import urllib.request
import urllib.error
import json

from django.shortcuts import render, redirect


# ──────────────────────────────────────────────
# Helper: fetch JSON from GitHub API
# ──────────────────────────────────────────────
def github_get(url):
    """
    Makes a GET request to the GitHub API and returns parsed JSON.
    Returns None if the request fails (repo not found, rate-limited, etc.)
    """
    req = urllib.request.Request(
        url,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'GitHubRepoAnalyzer/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError:
        return None
    except urllib.error.URLError:
        return None


# ──────────────────────────────────────────────
# Helper: parse owner and repo from a GitHub URL
# ──────────────────────────────────────────────
def parse_github_url(url):
    """
    Accepts:
      - https://github.com/owner/repo
      - github.com/owner/repo
      - owner/repo
    Returns (owner, repo) tuple or (None, None) if invalid.
    """
    url = url.strip().rstrip('/')

    # Full URL
    match = re.match(r'(?:https?://)?github\.com/([^/]+)/([^/]+)', url)
    if match:
        return match.group(1), match.group(2)

    # Short form: owner/repo
    match = re.match(r'^([^/]+)/([^/]+)$', url)
    if match:
        return match.group(1), match.group(2)

    return None, None


# ──────────────────────────────────────────────
# View: Home page
# ──────────────────────────────────────────────
def home(request):
    return render(request, 'analyzer/home.html')


# ──────────────────────────────────────────────
# View: Error page
# ──────────────────────────────────────────────
def error_page(request):
    return render(request, 'analyzer/error.html')


# ──────────────────────────────────────────────
# View: Analyze a repository
# ──────────────────────────────────────────────
def analyze(request):
    # Only accept POST (form submission from home page)
    if request.method != 'POST':
        return redirect('home')

    repo_url = request.POST.get('repo_url', '').strip()

    if not repo_url:
        return redirect('home')

    # Parse owner and repo name from the URL
    owner, repo = parse_github_url(repo_url)
    if not owner or not repo:
        return redirect('error')

    # ── 1. Fetch basic repo info ──────────────────
    repo_data = github_get(f'https://api.github.com/repos/{owner}/{repo}')
    if not repo_data:
        return redirect('error')

    # ── 2. Fetch commit activity (last 52 weeks) ──
    commit_data = github_get(
        f'https://api.github.com/repos/{owner}/{repo}/stats/commit_activity'
    )

    # We only show last 12 weeks
    weekly_commits = []
    if commit_data and isinstance(commit_data, list):
        last_12 = commit_data[-12:]          # last 12 weeks
        raw = [{'label': f'W{i}', 'total': w.get('total', 0)}
               for i, w in enumerate(last_12, 1)]

        max_val = max((w['total'] for w in raw), default=1) or 1
        for w in raw:
            # height as a percentage of the tallest bar (min 4 so it's visible)
            pct = max(4, round((w['total'] / max_val) * 100))
            weekly_commits.append({
                'label': w['label'],
                'total': w['total'],
                'height_pct': pct,
            })

    # ── 3. Fetch language breakdown ───────────────
    lang_data = github_get(
        f'https://api.github.com/repos/{owner}/{repo}/languages'
    )

    languages = []
    if lang_data and isinstance(lang_data, dict):
        total_bytes = sum(lang_data.values())
        colours = ['#22c55e', '#3b82f6', '#f97316', '#eab308',
                   '#ec4899', '#8b5cf6', '#06b6d4', '#64748b']
        for idx, (lang_name, byte_count) in enumerate(lang_data.items()):
            percentage = round((byte_count / total_bytes) * 100, 1)
            languages.append({
                'name': lang_name,
                'percentage': percentage,
                'color': colours[idx % len(colours)],
            })
        languages.sort(key=lambda x: x['percentage'], reverse=True)

        # ── Donut SVG math ──────────────────────────────────
        # r=40, circumference = 2 * pi * 40 = 251.33
        circumference = 251.33
        accumulated = 0.0
        for lang in languages:
            dash = round((lang['percentage'] / 100) * circumference, 2)
            lang['dash_array'] = f"{dash} {round(circumference - dash, 2)}"
            # dashoffset shifts the start point around the circle
            lang['dash_offset'] = round(circumference - accumulated, 2)
            accumulated += dash

    # ── 4. Fetch top contributors ─────────────────
    contrib_data = github_get(
        f'https://api.github.com/repos/{owner}/{repo}/contributors?per_page=5'
    )

    contributors = []
    if contrib_data and isinstance(contrib_data, list):
        for rank, person in enumerate(contrib_data[:5], 1):
            contributors.append({
                'rank': rank,
                'login': person.get('login', 'Unknown'),
                'avatar': person.get('avatar_url', ''),
                'contributions': person.get('contributions', 0),
            })

    # ── 5. Build context for the template ─────────
    context = {
        'repo_name':    repo_data.get('full_name', f'{owner}/{repo}'),
        'description':  repo_data.get('description', 'No description provided.'),
        'stars':        repo_data.get('stargazers_count', 0),
        'forks':        repo_data.get('forks_count', 0),
        'open_issues':  repo_data.get('open_issues_count', 0),
        'language':     repo_data.get('language', 'N/A'),
        'weekly_commits': weekly_commits,
        'languages':    languages,
        'contributors': contributors,
    }

    return render(request, 'analyzer/results.html', context)
