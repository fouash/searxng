# Complete SearXNG Deployment Guide

## Quick Start

### Pre-Deployment Validation

```bash
# Verify all components are ready
python3 scripts/validate_deployment.py

# Expected output: ✓ Deployment Status: READY
```

### Local Testing (Docker)

```bash
# Build the image
docker build -t searxng-render .

# Run the container
docker run -p 8080:8080 searxng-render

# Test in another terminal
curl "http://localhost:8080/search?q=aramco&format=json" | jq '.results | length'
```

### Render Deployment

1. **Push to GitHub**
   ```bash
   git push origin master
   ```

2. **Connect Render**
   - Go to https://dashboard.render.com
   - New > Web Service
   - Select this GitHub repository
   - Set Build Command: `python -m pip install -r requirements.txt`
   - Set Start Command: `/usr/local/searxng/render-entrypoint.sh`

3. **Monitor Deployment**
   - Check logs for startup errors
   - Wait for "✓ Downloaded Saudi domains database" message
   - Wait for "exec /usr/local/searxng/entrypoint.sh" confirmation

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────┐
│         SearXNG Render Instance                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Enabled Engines:                             │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Saudi Companies DB (Offline)               │  │
│  │   - 3,605 Saudi domains                      │  │
│  │   - 10 major company mappings                │  │
│  │   - Arabic/English support                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Disabled Archives (Render free tier):        │  │
│  ├──────────────────────────────────────────────┤  │
│  │ • Wayback Machine (700B+ pages)              │  │
│  │ • Common Crawl (80B+ web crawls)             │  │
│  │ • Memento Archive (federated search)         │  │
│  │ • Archive.today, Perma.cc, etc.             │  │
│  │                                              │  │
│  │ → Enable in settings.yml if upgrading       │  │
│  │   Render to Standard tier                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Data Files:                                       │
│  • /data/domains/saudi_domains.json (114 KB)       │
│  • /data/domains/company_mappings.json (2.8 KB)    │
│                                                     │
│  Port: 8080                                        │
│  Bandwidth: 5 GB/month (Render free tier)          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Features

### Saudi Companies Database

**Enabled by default.** Searches offline Saudi company domains without API calls.

**Features:**
- 3,605 verified Saudi domains from Certificate Transparency logs
- Arabic company name support (Aramco, STC, etc.)
- Fast lookup (~100ms)
- No external API dependencies
- Survives Render restarts

**Query Examples:**
- `aramco` → Returns aramco.com, aramco.com.sa, etc.
- `stc` → Returns Saudi Telecom domains
- `mobily` → Returns mobily.com.sa and related
- `bank` → Returns bank-related Saudi domains

### Internet Archive Integration

**Disabled by default.** Archive engines consume bandwidth and are disabled on Render free tier (5GB/month limit).

**To Enable Archives:**

1. Upgrade Render to Standard tier ($7/month) for full outbound access
2. Edit `container/settings.template.yml`
3. Change `disabled: true` to `disabled: false` for desired engines
4. Deploy

**Available Archives:**
- **Wayback Machine**: 700+ billion archived web pages (1996-present)
- **Common Crawl**: 80+ billion web crawl data
- **Memento Archive**: Federated time travel API across multiple archives
- **Archive.today**: Permanent preservation without deletion
- **Perma.cc**: Academic and legal citations (200M+ links)
- **Arquivo.pt**: Portuguese web archive (5B+ pages)
- **UK Web Archive**: UK-domain focused (parliament, museums, etc.)
- **Library of Congress**: US government and cultural heritage

## Troubleshooting

### "No Results Found" Error

If searches return no results (عفوا ! لم يتم العثور على نتائج):

**Step 1: Check Engine Data**
```bash
# Verify Saudi domains are loaded
python3 -c "import json; d=json.load(open('data/domains/saudi_domains.json')); print(f'Domains: {len(d[\"saudi_domains\"])}')"
```

**Step 2: Run Diagnostics**
```bash
# Check all components
python3 scripts/test_engines_direct.py

# If running, test API
python3 scripts/test_searxng_api.py --query aramco --full
```

**Step 3: Check Render Logs**
```bash
# In Render dashboard, go to Logs section
# Look for:
# - "Loaded 3605 Saudi domains"
# - "Engine: saudi_companies_db"
# - Any import or error messages
```

**Step 4: Verify Query Format**
- Queries must match domain keywords (e.g., "mobily", "aramco", "bank")
- Short queries (<3 chars) may not work
- Arabic queries supported if company mapping exists

### Docker Build Errors

**Error: `apk: not found`**
- ✓ Fixed in current version
- Uses `apk add --no-cache curl` (Alpine syntax)

**Error: `Module not found: markdown_it`**
- Only appears during testing outside container
- ✓ All dependencies included in Docker image
- ✓ SearXNG automatically installs on startup

### Search Engines Not Loading

**If archive engines show as disabled:**
- ✓ Correct for Render free tier (bandwidth limited)
- Archive engines disabled by default in settings.yml
- Change `disabled: false` to enable (requires Standard tier)

**If Saudi companies engine doesn't respond:**
1. Check data file exists: `ls -lh data/domains/saudi_domains.json`
2. Verify JSON format: `python3 -m json.tool data/domains/saudi_domains.json > /dev/null`
3. Check engine loads: `python3 scripts/validate_deployment.py`

## Performance Metrics

| Component | Metric | Notes |
|-----------|--------|-------|
| Saudi DB | <100ms | Local in-memory search |
| Wayback Machine | 1-3s | Archive CDX API query |
| Common Crawl | 2-4s | Metadata parsing |
| Memento | 3-5s | Federated search |
| Container Startup | ~10s | From Render restart |
| Data Download | ~5s | Saudi domains via Python script |

## Configuration Files

### Key Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage Alpine build |
| `container/settings.template.yml` | Engine configuration |
| `container/render-entrypoint.sh` | Render startup script |
| `searx/engines/saudi_companies_db.py` | Saudi companies engine |
| `data/domains/saudi_domains.json` | 3,605 Saudi domains |
| `data/domains/company_mappings.json` | Company name mappings |

### Required Python Packages

```
httpx          # HTTP requests
searxng        # Search engine
bottle         # Web framework
lxml           # XML parsing
python-dateutil # Date utilities
Brotli         # Compression
```

Additional for R2 storage:
```
boto3          # AWS S3/R2 client
```

## Maintenance

### Update Saudi Domains

```bash
# Download latest domains from Certificate Transparency logs
python3 scripts/download_saudi_domains.py

# Verify
python3 scripts/test_engines_direct.py
```

### Monitor Render Instance

```bash
# Check resource usage in Render dashboard
# Expected: <100MB RAM for Saudi DB engine
#          <1s response time per query
#          <1 KB per search (no compression)
```

### Enable R2 Persistent Storage

For stats persistence across Render restarts:

```bash
# Set Render environment variables
CLOUDFLARE_R2_ACCESS_KEY_ID=xxxxx
CLOUDFLARE_R2_SECRET_ACCESS_KEY=xxxxx
CLOUDFLARE_R2_ENDPOINT=https://xxxxx.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET=searxng
```

Stats auto-export to R2 every 30 minutes.

## Security

### Render Free Tier Limitations

- ✓ No outbound HTTPS access (archives disabled)
- ✓ 5GB/month bandwidth limit
- ✓ 512MB RAM limit
- ✓ No persistent disk between restarts

### Mitigation

- ✓ All data (domains) baked into image
- ✓ Offline-first approach (no external APIs)
- ✓ Auto-download on startup for live updates
- ✓ Optional R2 storage for stats

## Support & Debugging

### Quick Diagnostics

```bash
# Validate deployment
python3 scripts/validate_deployment.py

# Test data files
python3 scripts/test_engines_direct.py

# Test running instance
python3 scripts/test_searxng_api.py --full

# Check Render logs
# Dashboard > Logs > Check for errors
```

### Useful Commands

```bash
# Test with curl
curl "https://your-render-url.onrender.com/search?q=aramco&format=json" | jq '.results | length'

# Test specific engine
curl "https://your-render-url.onrender.com/search?q=mobily&engines=saudi_companies&format=json"

# Get preferences
curl "https://your-render-url.onrender.com/preferences"
```

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No results" | Run `python3 scripts/validate_deployment.py` |
| "Engine not found" | Verify engine file in `searx/engines/` |
| "Connection refused" | Ensure SearXNG is running and accessible |
| "Timeout" | Check Render logs for startup errors |
| "Import error" | All dependencies included in Docker - rebuild image |

## Next Steps

### For Development
1. Clone locally: `git clone https://github.com/fouash/searxng.git`
2. Run diagnostics: `python3 scripts/validate_deployment.py`
3. Test locally: `python3 scripts/test_engines_direct.py`
4. Modify and test in Docker

### For Production
1. Validate: `python3 scripts/validate_deployment.py`
2. Commit changes: `git push origin master`
3. Deploy to Render: Create new service
4. Monitor: Check logs and test search
5. Upgrade Archives: (Optional) Upgrade Render tier and enable archive engines

### For Integration
1. Integrate with saudidex-BE backend
2. Use `/search?q=<query>&format=json` API endpoint
3. Parse JSON results with title, url, engine fields
4. Cache results in backend if needed

## Additional Resources

- **SearXNG Docs**: https://docs.searxng.org/
- **Render Docs**: https://render.com/docs
- **Certificate Transparency**: https://crt.sh/
- **Archive APIs**:
  - Wayback: https://archive.org/help/wayback_api.php
  - Common Crawl: https://commoncrawl.org/overview
  - Memento: https://mementoweb.org/

## Support

For issues or questions:
1. Check DEBUGGING.md for troubleshooting
2. Run diagnostic tools (see above)
3. Review Render logs in dashboard
4. Check GitHub issues for similar problems
