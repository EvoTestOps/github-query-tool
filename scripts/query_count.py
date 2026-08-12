import os
import argparse
import tomllib

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

def count_repositories(query, samples):
    per_page = samples if samples > 0 else 1
    response = requests.get(
        "https://api.github.com/search/repositories",
        headers=HEADERS,
        params={
            "q": query,
            "per_page": per_page,
            "order": "desc",
            "sort": "stars",
            "page": 1,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()
    items = data.get("items", []) if samples > 0 else []
    return data.get("total_count", 0), items

SAMPLES = 3
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--samples", action="store_true")

    args = parser.parse_args()

    config = load_config(args.config)
    queries = get_queries(config)

    samples = SAMPLES if args.samples else 0

    for query in queries:
        total_count, items = count_repositories(query, samples)

        print(query)
        print(f"  total_count: {total_count}")
        for repo in items:
            print(f"{repo['full_name']}  Description: {repo['description']}")
        print()


if __name__ == "__main__":
    main()
