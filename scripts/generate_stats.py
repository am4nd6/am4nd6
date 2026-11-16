import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

username = os.environ["GITHUB_USERNAME"]
token = os.environ.get("GITHUB_TOKEN", "")
headers = {"Accept": "application/vnd.github+json", "User-Agent": username}
if token:
    headers["Authorization"] = f"Bearer {token}"


def api(url):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.load(response)


repos = []
repo_endpoint = ("https://api.github.com/user/repos?per_page=100&page="
                 if token else f"https://api.github.com/users/{username}/repos?per_page=100&page=")
page = 1
while True:
    suffix = "&affiliation=owner" if token else "&type=owner"
    batch = api(f"{repo_endpoint}{page}{suffix}")
    repos.extend(batch)
    if len(batch) < 100:
        break
    page += 1

languages = Counter()
for repo in repos:
    try:
        data = api(repo["languages_url"])
        languages.update(data)
    except urllib.error.HTTPError:
        pass

top_languages = languages.most_common(6)
total = len(repos)
private = sum(repo.get("private", False) for repo in repos)
public = total - private

pink = "#F5A9E1"
light = "#FCE7F3"
dark = "#24212B"

def card(title, lines, width=495):
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="220" viewBox="0 0 {width} 220">',
            f'<rect width="100%" height="100%" rx="18" fill="{dark}"/>',
            f'<text x="24" y="38" fill="{pink}" font-family="Arial" font-size="20" font-weight="bold">{title}</text>']
    for i, (label, value) in enumerate(lines):
        y = 78 + i * 25
        body.append(f'<text x="28" y="{y}" fill="{light}" font-family="Arial" font-size="15">{label}</text>')
        body.append(f'<text x="465" y="{y}" text-anchor="end" fill="{pink}" font-family="Arial" font-size="15" font-weight="bold">{value}</text>')
    body.append("</svg>")
    return "\n".join(body)

assets = Path("assets")
assets.mkdir(exist_ok=True)
(assets / "github-stats.svg").write_text(card("GitHub Statistics", [("Total repositories", total), ("Public repositories", public), ("Private repositories", private), ("Languages used", len(languages))]), encoding="utf-8")
(assets / "github-languages.svg").write_text(card("Most Used Languages", [(name, count) for name, count in top_languages] or [("No data yet", "-")]), encoding="utf-8")
