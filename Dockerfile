# syntax=docker/dockerfile:1
# SearXNG image for Railway. Saudi company discovery is runtime-driven;
# no Saudi company database is bundled into the image.

FROM docker.io/searxng/base:searxng-builder AS builder

COPY ./requirements.txt ./requirements-server.txt ./

ENV UV_NO_MANAGED_PYTHON="true" \
    UV_NATIVE_TLS="true"

ARG TIMESTAMP_VENV="0"
RUN set -eux -o pipefail; \
    export SOURCE_DATE_EPOCH="$TIMESTAMP_VENV"; \
    uv venv; \
    uv pip install --requirements ./requirements.txt --requirements ./requirements-server.txt; \
    uv cache prune --ci; \
    find ./.venv/lib/ -type f -exec strip --strip-unneeded {} + || true; \
    find ./.venv/lib/ -type d -name "__pycache__" -exec rm -rf {} +; \
    find ./.venv/lib/ -type f -name "*.pyc" -delete; \
    python -m compileall -q -f -j 0 --invalidation-mode=unchecked-hash ./.venv/lib/; \
    find ./.venv/lib/python*/site-packages/*.dist-info/ -type f -name "RECORD" -exec sort -t, -k1,1 -o {} {} \;; \
    find ./.venv/ -exec touch -h --date="@$TIMESTAMP_VENV" {} +

COPY --exclude=./searx/version_frozen.py ./searx/ ./searx/
RUN printf 'VERSION_STRING = "unknown"\nVERSION_TAG = "unknown"\nDOCKER_TAG = "unknown"\nGIT_URL = "unknown"\nGIT_BRANCH = "unknown"\n' > ./searx/version_frozen.py
RUN set -eux -o pipefail; \
    python -m compileall -q -f -j 0 --invalidation-mode=unchecked-hash ./searx/; \
    find ./searx/static/ -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) -exec gzip -9 -k {} + -exec brotli -9 -k {} + -exec gzip --test {}.gz + -exec brotli --test {}.br +

FROM docker.io/searxng/base:searxng AS dist

# The SearXNG base image is not Debian/Ubuntu and does not provide apt-get.
# Do not install curl/ca-certificates here; startup has no runtime download dependency.

COPY --chown=977:977 --from=builder /usr/local/searxng/.venv/ ./.venv/
COPY --chown=977:977 --from=builder /usr/local/searxng/searx/ ./searx/
COPY --chown=977:977 ./container/entrypoint.sh \
                      ./container/render-entrypoint.sh \
                      ./container/settings.template.yml \
                      ./container/settings.production.yml \
                      ./container/limiter.toml \
                      ./
RUN chmod +x ./render-entrypoint.sh

ARG VERSION="unknown"
ENV __SEARXNG_VERSION="$VERSION" \
    GRANIAN_PROCESS_NAME="searxng" \
    GRANIAN_INTERFACE="wsgi" \
    GRANIAN_HOST="::" \
    GRANIAN_PORT="8080" \
    GRANIAN_WEBSOCKETS="false" \
    GRANIAN_BLOCKING_THREADS="4" \
    GRANIAN_WORKERS_KILL_TIMEOUT="30s" \
    GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="5m"

EXPOSE 8080
ENTRYPOINT ["/usr/local/searxng/render-entrypoint.sh"]
