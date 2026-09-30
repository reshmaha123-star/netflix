"""Compatibility entry point for Streamlit Cloud deployments."""

from pathlib import Path
import runpy

# Run the dashboard on every Streamlit rerun; a regular import would be cached.
runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
