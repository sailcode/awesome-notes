import os
import requests
from datetime import datetime

USERNAME = os.environ["GITHUB_USERNAME"]

url = f"https://api.github.com/users/{USERNAME}/starred"

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}

repos = []
page = 1

while True:
    response = requests.get(
        url,
        headers=headers,
        params={
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "desc",
        },
    )
    response.raise_for_status()

    data = response.json()

    if not data:
        break

    repos.extend(data)

    if len(data) < 100:
        break

    page += 1


lines = []

lines.append("# ⭐ My GitHub Stars")
lines.append("")
lines.append(f"> 自动同步 GitHub Star 项目，共 **{len(repos)}** 个。")
lines.append("")
lines.append("| Project | Description | Language | Stars |")
lines.append("| --- | --- | --- | ---: |")

for repo in repos:
    name = repo["full_name"]
    repo_url = repo["html_url"]

    description = repo.get("description") or ""
    description = description.replace("|", "\\|").replace("\n", " ")

    language = repo.get("language") or "-"
    stars = repo.get("stargazers_count", 0)

    lines.append(
        f"| [{name}]({repo_url}) | {description} | {language} | ⭐ {stars:,} |"
    )

lines.append("")
lines.append(
    f"> Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
)

with open("stars.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
