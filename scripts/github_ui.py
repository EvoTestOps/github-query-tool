import streamlit as st
import time
import csv
import requests

from query_count import count_repositories, get_queries, HEADERS as COUNT_HEADERS

from github_search_to_csv import search_repositories, fetch_readme, HEADERS as SEARCH_HEADERS

st.set_page_config(
    page_title="GitHub query tool",
    layout="wide",
)

st.markdown(
    """
    <div class="app-header">
        <h1>GitHub Query Tool</h1>
        <p>Count repositories and export GitHub search results to CSV.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    div.stButton > button {
        border: 1px solid #000000;
        transition: all 0.15s ease-in-out;
    }

    div.stButton > button:hover {
        border-color: #000000;
        color: #000000;
        background-color: #eff6ff;
    }

    div.stButton > button:active {
        background-color: #dbeafe;
        transform: translateY(1px);
    }

    .app-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .app-header h1 {
        font-size: 3rem;
        margin-bottom: 0.25rem;
    }

    .app-header p {
        font-size: 1.05rem;
        color: #666666;
        margin-top: 0;
    }

    .results-placeholder {
        border: 1px solid #dddddd;
        border-radius: 0.75rem;
        padding: 2rem;
        min-height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
        color: #555555;
        background-color: #fafafa;
    }

    .results-placeholder h2 {
        margin-bottom: 0.5rem;
    }

    
    </style>
    """,
    unsafe_allow_html=True,
)

left_margin, left_column, middle_gap, right_column, right_margin = st.columns([0.25, 1.5, 0.25, 1.5, 0.25], gap="large")

with left_column:
    github_token = st.text_input("GitHub token", type="password", help="Provide a GitHub personal access token to increase the rate limit for API requests.")

    if github_token.strip():
        COUNT_HEADERS["Authorization"] = f"Bearer {github_token.strip()}"
        SEARCH_HEADERS["Authorization"] = f"Bearer {github_token.strip()}"
    else:
        COUNT_HEADERS.pop("Authorization", None)
        SEARCH_HEADERS.pop("Authorization", None)

    queries_text = st.text_area(
        "Queries",
        value='''"log anomaly" software,
    "log anomaly" system,
    "log-based anomaly" software,
    "log-based anomaly" system,
    "anomaly detection in log"''',
        height=250,
        help="Seperate queries by new lines. Each query will be combined with the selected filters to search for repositories."
    )

    search_name = st.checkbox("Search in name", value=True)
    search_description = st.checkbox("Search in description", value=True)
    search_readme = st.checkbox("Search in README", value=True)

    archived = st.checkbox("Include archived repositories", value=False)
    fork = st.checkbox("Include forks", value=False)

    stars = st.text_input("Stars", value="", help="Filter repositories by star count, for example: '>5'")
    size = st.text_input("Size", value="", help="Filter repositories by size in KB, for example: '>1000'")

    show_samples = st.checkbox("Show sample repositories of each query", value=False, help="Show top results for each query")

    sample_count = 0
    if show_samples:
        sample_count = st.number_input("Sample count", min_value=1, max_value=15, value=3)

    output_path = st.text_input("Output CSV path", value="data/log_analysis_repos.csv", help="Path for saving the CSV file with the search results.")

    def build_config():
        search_in = []

        if search_name:
            search_in.append("name")

        if search_description:
            search_in.append("description")

        if search_readme:
            search_in.append("readme")

        query_config = {
            "queries": [
                line.strip()
                for line in queries_text.splitlines()
                if line.strip()
            ],
            "search_in": search_in,
            "fork": fork
        }

        if not archived:
            query_config["archived"] = False
    

        if stars.strip():
            query_config["stars"] = stars.strip()

        if size.strip():
            query_config["size"] = size.strip()

        config = {
            "query": query_config
        }

        return config

    count_column, search_column, empty_column = st.columns([1, 1, 3], gap="small")

    with count_column:
        count_clicked = st.button("Count results")

    with search_column:
        search_clicked = st.button("Save results")

with right_column:
    if not count_clicked and not search_clicked:
        st.markdown(
            """
            <div class="results-placeholder">
                <h2>Results will appear here</h2>
                
            </div>
            """,
            unsafe_allow_html=True,
        )

    if count_clicked:
        st.subheader("Count results")
        config = build_config()

        queries = get_queries(config)

        samples = sample_count if show_samples else 0

        rows = []
        sample_results = []
        try:
            for query in queries:
                total_count, items = count_repositories(query, samples)

                rows.append(
                    {
                        "query": query,
                        "total_count": total_count
                    }
                )
                if items:
                    sample_results.append(
                        {
                            "query": query,
                            "total_count": total_count,
                            "items": items,
                        }
                    )

        except requests.exceptions.RequestException as e:
            st.error(f"GitHub request failed: {e}")

        st.dataframe(rows)

        if sample_results:
            st.subheader("Sample repositories")
            for result in sample_results:
                st.markdown(f"### {result['query']}")
                st.write(f"Total count: {result['total_count']}")

                for repo in result["items"]:
                    st.write(f"{repo['full_name']} — {repo.get('description') or ''}")

    if search_clicked:
        st.subheader("Saving results")
        log_box = st.container(height=300)
        log_area = log_box.empty()
        config = build_config()

        github_config = {
            "per_page": 100,
            "sleep_between_readmes": 0.2,
            "sleep_between_queries": 0
        }


        queries = get_queries(config)
        seen = {}
        rows = []
        logs = []
        try:
            for query in queries:
                repos = search_repositories(query, github_config)

                for repo in repos:
                    full_name = repo["full_name"]

                    if full_name in seen:
                        seen[full_name]["matched_queries"].append(query)
                        continue

                    owner = repo["owner"]["login"]
                    name = repo["name"]
                    logs.append(f"Fetching README: {full_name}")
                    log_area.text("\n".join(logs[-15:]))
                    readme = fetch_readme(owner, name)

                    row = {
                        "repository_name": full_name,
                        "description": repo.get("description") or "",
                        "html_url": repo["html_url"],
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language") or "",
                        "readme": readme,
                        "decision": "",
                        "reason": "",
                    }

                    seen[full_name] = {
                        "row": row,
                        "matched_queries": [query],
                    }
        except requests.exceptions.RequestException as e:
            st.error(f"GitHub request failed and search stopped: {e}")

        for item in seen.values():
            rows.append(item["row"])

        rows.sort(key=lambda r: int(r["stars"]), reverse=True)

        fieldnames = [
            "repository_name",
            "description",
            "html_url",
            "stars",
            "language",
            "readme",
            "decision",
            "reason",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logs.append(f"Wrote {len(rows)} unique repositories to {output_path}")
        log_area.text("\n".join(logs[-11:]))

