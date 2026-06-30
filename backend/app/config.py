import os
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    project_name = "Saville Fraud Royale Detector"
    clash_api_base_url = "https://api.clashroyale.com"
    clash_api_key = os.getenv("CLASH_ROYALE_API_KEY", "")
    use_mock_data = os.getenv("USE_MOCK_DATA", "true").lower() in {"1", "true", "yes", "on"}
    database_url = os.getenv("DATABASE_URL", "sqlite:///./reports.sqlite3")
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    project_root = _PROJECT_ROOT
    data_dir = project_root / "data"


settings = Settings()
