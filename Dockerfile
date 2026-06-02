FROM python:3.14-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_LOCKED=1
ENV UV_NO_DEV=1
ENV UV_NO_EDITABLE=1
ENV UV_PYTHON_DOWNLOADS=never
WORKDIR /app

RUN \
  --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --no-install-project

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync

FROM python:3.14-alpine

COPY --from=builder /app/.venv /app/.venv
ENTRYPOINT [ "/app/.venv/bin/gunicorn", "owe:create_app()" ]
