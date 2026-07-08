"""
Inlines waterfall_data.json into dashboard_template.html to produce the
final, self-contained arr_waterfall_dashboard.html. Run gen_dashboard.py
first to (re)generate waterfall_data.json from the current CSVs.
"""
import json
from pathlib import Path

base = Path(__file__).parent
data = json.loads((base / "waterfall_data.json").read_text())
template = (base / "dashboard_template.html").read_text()
out = template.replace("__DATA__", json.dumps(data, separators=(",", ":")))
(base / "arr_waterfall_dashboard.html").write_text(out)
print("wrote", base / "arr_waterfall_dashboard.html", "bytes:", len(out))
