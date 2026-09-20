FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY alembic.ini ./
COPY alembic ./alembic
RUN python -m pip install --no-cache-dir .

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app

USER app

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
