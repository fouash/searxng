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

# Ensure data/domains directory exists
mkdir -p /usr/local/searxng/data/domains

# Download Saudi domains if not present (for offline company search)
_domains_file="/usr/local/searxng/data/domains/saudi_domains.json"
if [ ! -f "${_domains_file}" ]; then
    echo "[searxng] Downloading Saudi company domains database..."

    if command -v python3 >/dev/null 2>&1 && [ -f "/usr/local/searxng/scripts/download_saudi_domains.py" ]; then
        # Use Python script if available
        python3 /usr/local/searxng/scripts/download_saudi_domains.py 2>&1 | grep -E "(Querying|Saved|Complete)" || true
    else
        # Fallback: Download from GitHub
        echo "[searxng] Fetching domains from GitHub..."
        if command -v curl >/dev/null 2>&1; then
            curl -s -f -o "${_domains_file}" \
                "https://raw.githubusercontent.com/fouash/searxng/master/data/domains/saudi_domains.json" 2>/dev/null && \
                echo "[searxng] ✓ Downloaded Saudi domains database" || \
                echo "[searxng] ⚠ Could not download domains - engine will return empty results"
        else
            echo "[searxng] ⚠ curl not found - cannot download domains"
        fi
    fi
fi

# Download company mappings if not present (for Arabic company name search)
_mappings_file="/usr/local/searxng/data/domains/company_mappings.json"
if [ ! -f "${_mappings_file}" ]; then
    echo "[searxng] Downloading company name mappings..."
    if command -v curl >/dev/null 2>&1; then
        curl -s -f -o "${_mappings_file}" \
            "https://raw.githubusercontent.com/fouash/searxng/master/data/domains/company_mappings.json" 2>/dev/null && \
            echo "[searxng] ✓ Downloaded company mappings (enables Arabic search)" || \
            echo "[searxng] ⚠ Could not download mappings - Arabic company search limited"
    else
        echo "[searxng] ⚠ curl not found - cannot download company mappings"
    fi
fi

# Initialize R2 bucket if credentials are provided
if [ -n "$CLOUDFLARE_R2_ACCESS_KEY_ID" ] && [ -n "$CLOUDFLARE_R2_SECRET_ACCESS_KEY" ]; then
    echo "[searxng] Initializing Cloudflare R2 bucket..."
    python3 /usr/local/searxng/scripts/init_r2.py >> /var/log/searxng-r2-init.log 2>&1 || \
        echo "[searxng] ⚠ R2 initialization failed - check credentials"
fi

# Auto-export stats to R2 every 30 minutes (if configured)
if [ -n "$CLOUDFLARE_R2_ACCESS_KEY_ID" ] && [ -n "$CLOUDFLARE_R2_SECRET_ACCESS_KEY" ]; then
    echo "[searxng] Starting R2 stats export daemon..."
    (
        while true; do
            sleep 1800  # 30 minutes
            python3 << 'PYTHON_SCRIPT'
try:
    import os
    from datetime import datetime

    # Only export if R2 is configured
    if os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID'):
        # Import after environment is set
        from searx.storage.r2_storage import R2Storage

        r2 = R2Storage()

        # Get current stats (placeholder - actual implementation depends on SearXNG stats module)
        stats_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'queries': 0,  # Would be populated from SearXNG stats
            'engines_checked': 1,
            'status': 'ok'
        }

        key = r2.save_stats(stats_data)
        print(f"[searxng] Exported stats to R2: {key}")
except Exception as e:
    print(f"[searxng] R2 export error: {e}")
PYTHON_SCRIPT
        done
    ) >> /var/log/searxng-r2-export.log 2>&1 &
fi

exec /usr/local/searxng/entrypoint.sh
