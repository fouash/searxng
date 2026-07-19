#!/bin/sh
# Render injects PORT at runtime; map it to GRANIAN_PORT before starting SearXNG.
export GRANIAN_PORT="${PORT:-8080}"

# Trust all upstream IPs for X-Forwarded-For so SearXNG sees the real client IP
# (Render's edge network terminates TLS and forwards via private IPs).
export GRANIAN_FORWARDED_ALLOW_IPS="${GRANIAN_FORWARDED_ALLOW_IPS:-*}"

# Copy limiter.toml template if not already present in the config directory.
_cfg="${__SEARXNG_CONFIG_PATH:-/etc/searxng}"
if [ ! -f "${_cfg}/limiter.toml" ]; then
    cp -f /usr/local/searxng/limiter.toml "${_cfg}/limiter.toml" 2>/dev/null || true
fi

# Download Saudi domains if not present (for offline company search)
_domains_file="/usr/local/searxng/data/domains/saudi_domains.json"
if [ ! -f "${_domains_file}" ]; then
    echo "[searxng] Downloading Saudi company domains database..."
    mkdir -p /usr/local/searxng/data/domains

    if command -v python3 >/dev/null 2>&1 && [ -f "/usr/local/searxng/scripts/download_saudi_domains.py" ]; then
        # Use Python script if available
        python3 /usr/local/searxng/scripts/download_saudi_domains.py 2>&1 | grep -E "(Querying|Saved|Complete)" || true
    else
        # Fallback: Download from GitHub
        echo "[searxng] Fetching domains from GitHub..."
        if command -v curl >/dev/null 2>&1; then
            curl -s -f -o "${_domains_file}" \
                "https://raw.githubusercontent.com/fouash/searxng/master/data/domains/saudi_domains.json" 2>/dev/null && \
                echo "[searxng] ✓ Downloaded Saudi domains database (4,260 domains)" || \
                echo "[searxng] ⚠ Could not download domains - engine will return empty results"
        else
            echo "[searxng] ⚠ curl not found - cannot download domains"
        fi
    fi
fi

exec /usr/local/searxng/entrypoint.sh
