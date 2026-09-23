import os
import json
import requests
from collections import Counter, defaultdict
from datetime import datetime, timezone

USERNAME = os.environ["GITHUB_USERNAME"]

API_URL = f"https://api.github.com/users/{USERNAME}/starred"

headers = {
    "Accept": "application/vnd.github.star+json",
    "X-GitHub-Api-Version": "2026-03-10",
}

all_stars = []
page = 1

while True:
    response = requests.get(
        API_URL,
        headers=headers,
        params={
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "desc",
        },
        timeout=30,
    )

    response.raise_for_status()
    items = response.json()

    if not items:
        break

    all_stars.extend(items)

    if len(items) < 100:
        break

    page += 1


stars = []

for item in all_stars:
    repo = item["repo"]

    stars.append({
        "name": repo["name"],
        "full_name": repo["full_name"],
        "url": repo["html_url"],
        "description": repo.get("description"),
        "language": repo.get("language"),
        "topics": repo.get("topics", []),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "archived": repo.get("archived", False),
        "homepage": repo.get("homepage"),
        "starred_at": item.get("starred_at"),
    })


# -------------------------
# 保存 JSON
# -------------------------

os.makedirs("data", exist_ok=True)

with open("data/stars.json", "w", encoding="utf-8") as f:
    json.dump(
        stars,
        f,
        ensure_ascii=False,
        indent=2,
    )


# -------------------------
# 分类
# -------------------------

CATEGORY_RULES = {
    "AI / Agent": {
        "ai",
        "llm",
        "agent",
        "agents",
        "langchain",
        "rag",
        "machine-learning",
        "deep-learning",
        "artificial-intelligence",
    },

    "Frontend": {
        "react",
        "vue",
        "frontend",
        "typescript",
        "javascript",
        "ui",
        "css",
    },

    "Backend": {
        "backend",
        "api",
        "server",
        "spring",
        "fastapi",
        "django",
        "nodejs",
    },

    "Database": {
        "database",
        "mysql",
        "postgresql",
        "mongodb",
        "redis",
        "sql",
    },

    "DevTools": {
        "developer-tools",
        "cli",
        "terminal",
        "vscode",
        "ide",
        "devtools",
    },
}


def classify(repo):
    topics = set(t.lower() for t in repo["topics"])

    for category, keywords in CATEGORY_RULES.items():
        if topics & keywords:
            return category

    language = (repo["language"] or "").lower()

    if language in {"typescript", "javascript", "html", "css"}:
        return "Frontend"

    return "Others"


categories = defaultdict(list)

for repo in stars:
    categories[classify(repo)].append(repo)


# -------------------------
# 生成 stars.md
# -------------------------

lines = []

lines.append("# ⭐ GitHub Stars")
lines.append("")
lines.append(
    f"共收藏 **{len(stars)}** 个 GitHub 项目。"
)
lines.append("")

category_order = [
    "AI / Agent",
    "Frontend",
    "Backend",
    "Database",
    "DevTools",
    "Others",
]

for category in category_order:

    repos = categories.get(category)

    if not repos:
        continue

    lines.append(f"## {category}")
    lines.append("")

    for repo in repos:

        desc = repo["description"] or ""
        language = repo["language"] or "Unknown"

        date = ""

        if repo["starred_at"]:
            date = repo["starred_at"][:10]

        lines.append(
            f"### [{repo['full_name']}]({repo['url']})"
        )

        lines.append("")

        if desc:
            lines.append(desc)
            lines.append("")

        lines.append(
            f"`{language}` · ⭐ {repo['stars']:,} · Starred {date}"
        )

        if repo["topics"]:
            lines.append("")
            lines.append(
                " ".join(
                    f"`{topic}`"
                    for topic in repo["topics"][:8]
                )
            )

        lines.append("")


with open("stars.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))


# -------------------------
# README
# -------------------------

languages = Counter(
    repo["language"]
    for repo in stars
    if repo["language"]
)

top_languages = languages.most_common(10)

readme = []

readme.append("# My GitHub Stars")
readme.append("")
readme.append(
    "自动同步和整理我在 GitHub 收藏的开源项目。"
)
readme.append("")

readme.append("## 📊 Statistics")
readme.append("")
readme.append(f"- ⭐ Total: **{len(stars)}**")
readme.append(
    f"- 📂 Categories: **{len([x for x in categories.values() if x])}**"
)
readme.append("")

readme.append("### Languages")
readme.append("")

for language, count in top_languages:
    readme.append(
        f"- {language}: {count}"
    )

readme.append("")
readme.append(
    "👉 [查看全部收藏](stars.md)"
)
readme.append("")

readme.append(
    f"_Last updated: "
    f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(readme))
