import json
from pathlib import Path

def set_json(key: str, value: dict):
	path = Path("blob_store") / f"{key}.json"
	path.parent.mkdir(exist_ok=True)
	path.write_text(json.dumps(value))

def get_json(key: str) -> dict | None:
	path = Path("blob_store") / f"{key}.json"
	if not path.exists():
		return None
	return json.loads(path.read_text())
