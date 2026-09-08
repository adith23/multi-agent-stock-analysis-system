# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS dependencies

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY backend/requirements/ /tmp/requirements/
# Installing the CPU wheel explicitly prevents pip from selecting a CUDA build.
RUN python -m pip install --upgrade pip \
    && python -m pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r /tmp/requirements/prod.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:${PATH}

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home app

WORKDIR /app
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin
COPY backend/ ./
COPY docker/entrypoint.sh /usr/local/bin/stockanalysis-entrypoint

RUN chmod +x /usr/local/bin/stockanalysis-entrypoint \
    && DJANGO_SETTINGS_MODULE=config.settings.production \
       DJANGO_SECRET_KEY=build-only-not-used-at-runtime \
       DJANGO_ALLOWED_HOSTS=localhost \
       TASK_BACKEND=cloud_tasks \
       python manage.py collectstatic --noinput \
    && chown -R app:app /app

USER app
EXPOSE 8000
ENTRYPOINT ["stockanalysis-entrypoint"]
CMD ["gunicorn", "config.asgi:application", "--config", "config/gunicorn.py"]
