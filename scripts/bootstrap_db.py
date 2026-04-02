from mygooglealertpapers.config import load_settings
from mygooglealertpapers.db.schema import create_schema_at_default_path


if __name__ == "__main__":
    settings = load_settings()
    create_schema_at_default_path(settings.sqlite_path)
    print(f"Initialized DB at {settings.sqlite_path}")
