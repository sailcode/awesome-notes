import os
import json
import requests
from collections import Counter, defaultdict
from datetime import datetime, timezone


USERNAME = os.environ["GITHUB_USERNAME"]

API_URL = f"https://api.github.com/users/{USERNAME}/starred"

HEADERS = {
    "Accept": "application/vnd.github.star+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


CATEGORY_RULES = {
    "🤖 AI / Agent": {
        "ai",
        "artificial-intelligence",
        "llm",
        "agent",
        "agents",
        "rag",
        "langchain",
        "langgraph",
        "machine-learning",
        "deep-learning",
        "generative-ai",
        "chatgpt",
        "openai",
        "copilot",
    },
    "🎨 Frontend": {
        "frontend",
        "react",
        "vue",
        "svelte",
        "javascript",
        "typescript",
        "css",
        "html",
        "ui",
        "web",
        "webapp",
    },
    "⚙️ Backend": {
        "backend",
        "server",
        "api",
        "fastapi",
        "django",
        "spring",
        "spring-boot",
        "nodejs",
        "microservices",
        "grpc",
    },
    "🗄️ Database": {
        "database",
        "mysql",
        "postgresql",
        "mongodb",
        "redis",
        "sqlite",
        "sql",
        "vector-database",
    },
    "🛠️ DevTools": {
        "cli",
        "terminal",
        "developer-tools",
        "devtools",
        "vscode",
        "ide",
        "git",
        "github",
        "docker",
        "kubernetes",
        "automation",
    },
}


CATEGORY_ORDER = [
    "🤖 AI / Agent",
    "🎨 Frontend",
    "⚙️ Backend",
    "🗄️ Database",
    "🛠️ DevTools",
    "📦 Others",
]


def format_number(number):
    if number >= 1_000_000:
        value = number / 1_000_000
        return f"{value:.1f}m".rstrip("0").rstrip(".")

    if number >= 1_000:
        value = number / 1_000
        return f"{value:.1f}k".rstrip("0").rstrip(".")

    return str(number)


def clean_description(description):
    if not description:
        return "No description."

    description = description.replace("\n", " ").strip()

    while "  " in description:
        description = description.replace("  ", " ")

    return description


def markdown_escape(text):
    if not text:
        return text

    return (
        text
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def category_anchor(category):
    value = category

    for emoji in ["🤖", "🎨", "⚙️", "🗄️", "🛠️", "📦"]:
        value = value.replace(emoji, "")

    value = value.strip().lower()
    value = value.replace(" / ", "--")
    value = value.replace("/", "")
    value = value.replace(" ", "-")

    return value


def classify_repo(repo):
    topics = {
        topic.lower()
        for topic in repo.get("topics", [])
    }

    language = (repo.get("language") or "").lower()

    name_text = (
        repo.get("full_name", "")
        + " "
        + (repo.get("description") or "")
    ).lower()

    for category, keywords in CATEGORY_RULES.items():
        if topics & keywords:
            return category

        for keyword in keywords:
            if keyword in name_text:
                return category

    if language in {
        "typescript",
        "javascript",
        "html",
        "css",
        "vue",
        "svelte",
    }:
        return "🎨 Frontend"

    return "📦 Others"


def fetch_starred_repositories():
    all_items = []

    page = 1

    while True:
        print(f"Fetching page {page}...")

        response = requests.get(
            API_URL,
            headers=HEADERS,
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

        all_items.extend(items)

        if len(items) < 100:
            break

        page += 1

    return all_items


def normalize_repositories(items):
    repositories = []

    for item in items:
        repo = item["repo"]

        repository = {
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "url": repo.get("html_url"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "topics": repo.get("topics", []),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "watchers": repo.get("watchers_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "archived": repo.get("archived", False),
            "fork": repo.get("fork", False),
            "homepage": repo.get("homepage"),
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "starred_at": item.get("starred_at"),
        }

        repository["category"] = classify_repo(repository)

        repositories.append(repository)

    return repositories


def save_json(repositories):
    os.makedirs("data", exist_ok=True)

    with open(
        "data/stars.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            repositories,
            file,
            ensure_ascii=False,
            indent=2,
        )


def generate_stars_markdown(repositories):
    categories = defaultdict(list)

    for repo in repositories:
        categories[repo["category"]].append(repo)

    for repos in categories.values():
        repos.sort(
            key=lambda item: item.get("stars", 0),
            reverse=True,
        )

    updated_at = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    lines = []

    lines.append("# Awesome GitHub Stars")
    lines.append("")
    lines.append(
        "> A curated collection of repositories "
        "I've starred on GitHub."
    )
    lines.append("")
    lines.append(
        f"**{len(repositories)} repositories "
        f"· Last updated {updated_at}**"
    )
    lines.append("")

    lines.append("## Contents")
    lines.append("")

    for category in CATEGORY_ORDER:
        repos = categories.get(category)

        if not repos:
            continue

        anchor = category_anchor(category)

        lines.append(
            f"- [{category}](#{anchor}) "
            f"({len(repos)})"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    for category in CATEGORY_ORDER:
        repos = categories.get(category)

        if not repos:
            continue

        lines.append(f"## {category}")
        lines.append("")

        for repo in repos:
            full_name = repo["full_name"]
            url = repo["url"]

            description = markdown_escape(
                clean_description(
                    repo.get("description")
                )
            )

            language = repo.get("language")
            stars = repo.get("stars", 0)

            meta = []

            if language:
                meta.append(f"`{language}`")

            meta.append(
                f"⭐ {format_number(stars)}"
            )

            if repo.get("archived"):
                meta.append("`Archived`")

            meta_text = " ".join(meta)

            lines.append(
                f"- [{full_name}]({url})"
                f" - {description} "
                f"{meta_text}"
            )

        lines.append("")

    with open(
        "stars.md",
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(lines))


def generate_readme(repositories):
    languages = Counter(
        repo["language"]
        for repo in repositories
        if repo.get("language")
    )

    categories = Counter(
        repo["category"]
        for repo in repositories
    )

    top_languages = languages.most_common(10)

    updated_at = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")

    lines = []

    lines.append("# ⭐ My GitHub Stars")
    lines.append("")
    lines.append(
        "> Automatically synchronized collection "
        "of repositories I've starred on GitHub."
    )
    lines.append("")

    lines.append(
        f"**Total: {len(repositories)} repositories**"
    )
    lines.append("")

    lines.append("## 📚 Browse")
    lines.append("")
    lines.append(
        "👉 **[View all starred repositories](stars.md)**"
    )
    lines.append("")

    lines.append("## 📂 Categories")
    lines.append("")

    for category in CATEGORY_ORDER:
        count = categories.get(category, 0)

        if count == 0:
            continue

        anchor = category_anchor(category)

        lines.append(
            f"- [{category}](stars.md#{anchor}) "
            f"— {count}"
        )

    lines.append("")

    if top_languages:
        lines.append("## 💻 Languages")
        lines.append("")

        for language, count in top_languages:
            lines.append(
                f"- **{language}** — {count}"
            )

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "Automatically synchronized by "
        "GitHub Actions."
    )
    lines.append("")
    lines.append(
        f"_Last updated: {updated_at}_"
    )

    with open(
        "README.md",
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(lines))


def main():
    print(
        f"Syncing starred repositories for: "
        f"{USERNAME}"
    )

    items = fetch_starred_repositories()

    print(
        f"Found {len(items)} starred repositories."
    )

    repositories = normalize_repositories(items)

    save_json(repositories)

    generate_stars_markdown(repositories)

    generate_readme(repositories)

    print("Done.")
    print("- README.md updated")
    print("- stars.md updated")
    print("- data/stars.json updated")


if __name__ == "__main__":
    main()
