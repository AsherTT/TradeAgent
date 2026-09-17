"""Celery worker entry point and configuration smoke check."""

import sys

from backend.app.jobs import celery_app


def main() -> int:
    print(f"Celery worker configured for app {celery_app.main}.")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    sys.exit(main())
