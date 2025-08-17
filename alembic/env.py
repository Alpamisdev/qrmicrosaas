from __future__ import annotations

from logging.config import fileConfig
import os
from pathlib import Path
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # Logging config is optional; proceed without if minimal ini
        pass

# Add your model's MetaData object here for 'autogenerate' support
# Ensure project root is on sys.path so 'app' can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import Base  # type: ignore
from app import models  # noqa: F401
target_metadata = Base.metadata


def get_url() -> str:
    # Load .env files so DATABASE_URL is available
    try:
        from dotenv import load_dotenv
        # Try both project root and app/.env
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / '.env')
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / 'app' / '.env')
    except Exception:
        pass

    url = os.getenv("DATABASE_URL", "")
    # Use sync driver for Alembic if an async driver is configured
    if url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite+aiosqlite", "sqlite", 1)
    return url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


