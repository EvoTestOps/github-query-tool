import base64
import csv
import os
import argparse
import tomllib
import datetime

import requests


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

session = requests.Session()




def load_config(config_path):
    with open(config_path, "rb") as file:
        return tomllib.load(file)


def get_queries(config):
    query_config = config["query"]

    queries = query_config["queries"]

    archived = query_config.get("archived")
    fork = query_config.get("fork")
    search_in = query_config.get("search_in", ["name", "description", "readme"])
    stars = query_config.get("stars")
    size = query_config.get("size")
    qualifiers = []

    if search_in:
        qualifiers.append("in:" + ",".join(search_in))

    if archived is not None:
        qualifiers.append(f"archived:{str(archived).lower()}")

    if fork is not None:
        qualifiers.append(f"fork:{str(fork).lower()}")

    if stars is not None:
        qualifiers.append(f"stars:{stars}")

    if size is not None:
        qualifiers.append(f"size:{size}")

    final_queries = []

    for query in queries:
        parts = [query]
        parts.extend(qualifiers)
        final_queries.append(" ".join(parts))

    return final_queries



def github_get(url, params=None):
    response = session.get(url, headers=HEADERS, params=params, timeout=30)

    if response.status_code in (403, 429):
        print("Rate limit or forbidden response:")
        print(response.text[:500])

        response = session.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30,
        )

    response.raise_for_status()
    return response.json()

GITHUB_SEARCH_START = datetime.datetime(2008, 1, 1, tzinfo=datetime.timezone.utc)
 
 
def gh_dt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def search_repositories(query, github_config):
    repos = []

    per_page = github_config.get("per_page", 100)

    now = datetime.datetime.now(datetime.timezone.utc)
    windows = [(GITHUB_SEARCH_START, now)]

    while windows:
        lo, hi = windows.pop()
        windowed_query = f"{query} created:{gh_dt(lo)}..{gh_dt(hi)}"
 
        page = 1
        while True:
            try:
                data = github_get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": windowed_query,
                        "per_page": per_page,
                        "page": page,
                    },
                )
            except requests.HTTPError as error:
                if error.response is not None and error.response.status_code == 422:
                    print(f"Stopping at page {page}. No more search results")
                    break

                raise
            if page == 1:
                total = data.get("total_count", 0)
                if total > 1000 and (hi - lo) > datetime.timedelta(seconds=1):
                    mid = (lo + (hi - lo) / 2).replace(microsecond=0)
                    windows.append((lo, mid))
                    windows.append((mid + datetime.timedelta(seconds=1), hi))
                    break



            items = data.get("items", [])
            repos.extend(items)

            if len(items) < per_page:
                break

            page +=1

    return repos


def fetch_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    try:
        data = github_get(url)
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            return ""
        print(f"HTTP error")
        return ""
    except requests.exceptions.RequestException as error:
        print(f"Network error")
        return ""

    content = data.get("content", "")
    encoding = data.get("encoding")
    if encoding == "base64":
        return base64.b64decode(content).decode("utf-8", errors="replace")

    return content



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        required=True
    )
    parser.add_argument(
        "--output",
        default=None
    )

    args = parser.parse_args()

    config = load_config(args.config)
    github_config = config["github"]

    output_path = args.output or config["output"]["path"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    queries = get_queries(config)

    print("Generated the following GitHub queries:")
    for query in queries:
        print(f"  - {query}")

    seen = {}
    rows = []

    for query in queries:
        print(f"Searching query: {query}")
        repos = search_repositories(query, github_config)

        for repo in repos:
            full_name = repo["full_name"]

            if full_name in seen:
                seen[full_name]["matched_queries"].append(query)
                continue

            owner = repo["owner"]["login"]
            name = repo["name"]

            
            readme = fetch_readme(owner, name)
            print(f"Fetched: {full_name}")

            row = {
                "repository_title": full_name,
                "description": repo.get("description") or "",
                "html_url": repo["html_url"],
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language") or "",
                "readme": readme,
            }

            seen[full_name] = {
                "row": row,
                "matched_queries": [query],
            }


    for item in seen.values():
        rows.append(item["row"])

    rows.sort(key=lambda r: int(r["stars"]), reverse=True)

    fieldnames = [
        "repository_title",
        "description",
        "html_url",
        "stars",
        "language",
        "readme",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} unique repositories to {output_path}")


if __name__ == "__main__":
    main()
