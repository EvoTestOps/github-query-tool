## Requirements

- Python 3.11+
- GitHub personal access token recommended

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Streamlit UI

Start the UI from the repository root:

```bash
streamlit run scripts/github_ui.py
```

## Running from the command line

Set a GitHub token:

```bash
export GITHUB_TOKEN="your_token_here"
```

Run the repository search tool in the repository root:

```bash
python3 scripts/github_search_to_csv.py --config configs/log_analysis.toml
```

The output path is defined in the config file.

## Count query results

To count how many repositories each query matches:

```bash
python3 scripts/query_count.py --config configs/log_analysis.toml
```

Also show sample repositories:

```bash
python3 scripts/query_count.py --config configs/log_analysis.toml --samples
```
