# warn-tracker
This is a project of [What We Will](https://wwwrise.org) to track [WARN Act](https://www.ecfr.gov/current/title-20/chapter-V/part-639) filings across the US.

## how to run

- (if you don't have `uv` installed)
  - `brew install uv` on Mac
  - `pip install uv` otherwise
- `uv venv warn-tracker`
- `source warn-tracker/bin/activate` # `deactivate` to exit
- `uv sync`
- `streamlit run warn_tracker_dashboard.py`

or view it here: https://warn-tracker.streamlit.app
