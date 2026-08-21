#!/bin/sh
# Railway/Render-compatible SearXNG startup.
set -eu

export GRANIAN_PORT="${PORT:-8080}"
export GRANIAN_FORWARDED_ALLOW_IPS="${GRANIAN_FORWARDED_ALLOW_IPS:-*}"

_cfg="${__SEARXNG_CONFIG_PATH:-/etc/searxng}"
if [ ! -f "${_cfg}/limiter.toml" ]; then
    cp -f /usr/local/searxng/limiter.toml "${_cfg}/limiter.toml" 2>/dev/null || true
fi

# The Saudi datasets are shipped in the repository. Prefer the bundled copy;
# only download when the image does not contain them. This removes the old
# Render-only runtime dependency on curl/network access.
mkdir -p /usr/local/searxng/data/domains

_domains_file="/usr/local/searxng/data/domains/saudi_domains.json"
_repo_domains="/usr/local/searxng/data/domains/saudi_domains.json"
if [ ! -s "${_domains_file}" ] && [ -s "${_repo_domains}" ]; then
    cp "${_repo_domains}" "${_domains_file}"
fi

if [ ! -s "${_domains_file}" ]; then
    echo "[searxng] Saudi domains dataset missing; attempting download..."
    curl -sSfL -o "${_domains_file}.tmp" \
        "https://raw.githubusercontent.com/fouash/searxng/master/data/domains/saudi_domains.json" \
        && mv "${_domains_file}.tmp" "${_domains_file}" \
        || { rm -f "${_domains_file}.tmp"; echo "[searxng] ERROR: Saudi domains dataset unavailable" >&2; exit 1; }
fi

_mappings_file="/usr/local/searxng/data/domains/company_mappings.json"
if [ ! -s "${_mappings_file}" ]; then
    echo "[searxng] Downloading company name mappings..."
    curl -sSfL -o "${_mappings_file}.tmp" \
        "https://raw.githubusercontent.com/fouash/searxng/master/data/domains/company_mappings.json" \
        && mv "${_mappings_file}.tmp" "${_mappings_file}" \
        || { rm -f "${_mappings_file}.tmp"; echo "[searxng] WARNING: company mappings unavailable" >&2; }
fi

echo "[searxng] Saudi domains dataset ready: $(wc -c < "${_domains_file}") bytes"
[ -s "${_mappings_file}" ] && echo "[searxng] Company mappings ready: $(wc -c < "${_mappings_file}") bytes" || true

if [ -n "${CLOUDFLARE_R2_ACCESS_KEY_ID:-}" ] && [ -n "${CLOUDFLARE_R2_SECRET_ACCESS_KEY:-}" ]; then
    echo "[searxng] Initializing Cloudflare R2 bucket..."
    python3 /usr/local/searxng/scripts/init_r2.py >> /var/log/searxng-r2-init.log 2>&1 || \
        echo "[searxng] WARNING: R2 initialization failed - check credentials"
fi

exec /usr/local/searxng/entrypoint.sh
