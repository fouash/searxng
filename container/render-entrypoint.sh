#!/bin/sh
# Railway-compatible SearXNG startup.
# Saudi company discovery is runtime-driven; no company database is required.
set -eu

export GRANIAN_PORT="${PORT:-8080}"
export GRANIAN_FORWARDED_ALLOW_IPS="${GRANIAN_FORWARDED_ALLOW_IPS:-*}"

_cfg="${__SEARXNG_CONFIG_PATH:-/etc/searxng}"
if [ ! -f "${_cfg}/limiter.toml" ]; then
    cp -f /usr/local/searxng/limiter.toml "${_cfg}/limiter.toml" 2>/dev/null || true
fi

# Do not download or load a Saudi company database during startup.
# Discovery is performed continuously by the application/search engines,
# with validation and deduplication downstream in saudidex-BE.
echo "[searxng] Saudi company discovery mode: runtime"

echo "[searxng] Starting SearXNG..."
exec /usr/local/searxng/entrypoint.sh
