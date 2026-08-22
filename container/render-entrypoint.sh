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

# Install the explicit production configuration before the upstream entrypoint.
# This prevents the upstream image from silently generating settings.yml from
# its generic template and ensures Railway runs the SaudiDex engine allowlist.
if [ ! -f "${_cfg}/settings.yml" ]; then
    if [ ! -f /usr/local/searxng/settings.production.yml ]; then
        echo "[searxng] ERROR: bundled production settings are missing" >&2
        exit 1
    fi
    cp -f /usr/local/searxng/settings.production.yml "${_cfg}/settings.yml"
    echo "[searxng] Loaded bundled production settings.yml"
else
    echo "[searxng] Using existing production settings.yml"
fi

# Never allow SearXNG's documented insecure placeholder secret to reach startup.
# Generate a per-container secret when the bundled config still contains the
# placeholder. This keeps the secret out of Git and makes every deployment safe.
if grep -q 'secret_key: "ultrasecretkey"' "${_cfg}/settings.yml"; then
    _secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
    sed -i "s/secret_key: \"ultrasecretkey\"/secret_key: \"${_secret}\"/" "${_cfg}/settings.yml"
    echo "[searxng] Generated runtime server secret"
fi

# Fail fast if the production configuration was not actually installed.
if ! grep -q '^server:' "${_cfg}/settings.yml"; then
    echo "[searxng] ERROR: production server configuration is missing" >&2
    exit 1
fi
if ! grep -q '^engines:' "${_cfg}/settings.yml"; then
    echo "[searxng] ERROR: production engine configuration is missing" >&2
    exit 1
fi
if [ ! -s "${_cfg}/settings.yml" ]; then
    echo "[searxng] ERROR: settings.yml is empty" >&2
    exit 1
fi

echo "[searxng] Saudi company discovery mode: runtime"
echo "[searxng] Starting SearXNG..."
exec /usr/local/searxng/entrypoint.sh
