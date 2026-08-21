FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app

COPY backend/requirements/ /tmp/requirements/
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements/prod.txt

COPY backend/ /app/
COPY docker/entrypoint.sh /usr/local/bin/stockanalysis-entrypoint

RUN chmod +x /usr/local/bin/stockanalysis-entrypoint \
    && chown -R app:app /app

USER app

EXPOSE 8000
ENTRYPOINT ["stockanalysis-entrypoint"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-"]

