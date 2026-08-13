# GitHub Repository Collector

Searches GitHub for repositories matching configurable queries and exports the results to CSV. The output is formatted to be compatible with [AiSysRev](https://github.com/EvoTestOps/AISysRev) for screening GitHub repositories in a systematic literature review.

## Requirements

- Python 3.11+
- GitHub personal access token recommended

## Install dependencies

This project supports [uv](https://docs.astral.sh/uv/) (recommended) or plain pip.

### Using uv (recommended)

`uv` creates an isolated `.venv` in the repo instead of installing into your default/global environment:

```bash
uv sync
```

Then prefix commands below with `uv run`, e.g. `uv run streamlit run scripts/github_ui.py`.

### Using pip

```bash
pip install -r requirements.txt
```

## Running the Streamlit UI

Start the UI from the repository root:

```bash
streamlit run scripts/github_ui.py
# or with uv:
uv run streamlit run scripts/github_ui.py
```

## Running from the command line

Set a GitHub token:

```bash
export GITHUB_TOKEN="your_token_here"
```

Run the repository search tool in the repository root:

```bash
python3 scripts/github_search_to_csv.py --config configs/log_analysis.toml
# or with uv:
uv run scripts/github_search_to_csv.py --config configs/log_analysis.toml
```

The output path is defined in the config file.

## Count query results

To count how many repositories each query matches:

```bash
python3 scripts/query_count.py --config configs/log_analysis.toml
# or with uv:
uv run scripts/query_count.py --config configs/log_analysis.toml
```

Also show sample repositories:

```bash
python3 scripts/query_count.py --config configs/log_analysis.toml --samples
```
