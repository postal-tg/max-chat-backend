from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> None:
    project_root = Path.cwd()
    if not (project_root / "alembic.ini").exists():
        project_root = Path(__file__).resolve().parents[3]
    alembic_config = Config(str(project_root / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(project_root / "migrations"))
    command.upgrade(alembic_config, "head")


if __name__ == "__main__":
    main()

