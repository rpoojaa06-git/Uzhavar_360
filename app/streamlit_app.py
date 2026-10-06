import sys
from pathlib import Path

# Add project root to path so all imports work seamlessly
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Execute the main streamlit_app
app_file = root_dir / "streamlit_app.py"
with open(app_file, encoding="utf-8") as f:
    code = f.read()

exec(compile(code, str(app_file), "exec"))
