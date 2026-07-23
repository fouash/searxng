# SearXNG Debugging Guide

## No Results Found Issue

If you see "عفوا ! لم يتم العثور على نتائج" (Sorry! No results found) when searching:

### 1. Verify Engine Data

Check that the Saudi domains database is loaded:

```bash
# Check file exists and has content
ls -lh data/domains/saudi_domains.json
wc -l data/domains/saudi_domains.json

# Verify JSON is valid
python3 -c "import json; data=json.load(open('data/domains/saudi_domains.json')); print(f'Domains: {len(data[\"saudi_domains\"])}')"
```

### 2. Test the Engine Directly

```bash
# From the SearXNG container or with dependencies installed:
python3 scripts/test_engines_direct.py
```

This will show:
- ✓ Saudi domains loaded (3,605 domains)
- ✓ Company mappings (10 entries)
- ✓ All engine files present
- ✓ Settings configuration valid

### 3. Test via SearXNG API

Once the SearXNG server is running (e.g., at http://localhost:8080):

```bash
# Test the Saudi companies engine
curl "http://localhost:8080/search?q=aramco&format=json" | jq '.results | length'

# Test with shortcut
curl "http://localhost:8080/search?q=mobily&format=json" | jq '.results'

# Test a specific engine
curl "http://localhost:8080/search?q=test&engines=saudi_companies&format=json"
```

### 4. Check Server Logs

If running in Docker/Render:

```bash
# View container logs
docker logs <container_id>

# Look for engine loading errors
docker logs <container_id> | grep -i "saudi\|engine\|error"
```

### 5. Common Issues

| Issue | Solution |
|-------|----------|
| "Engine not found" | Verify `searx/engines/saudi_companies_db.py` exists |
| "Database not loaded" | Check `data/domains/saudi_domains.json` is readable |
| "Import error" | Ensure all dependencies in `requirements.txt` are installed |
| "No match for query" | Queries must contain text from domain names (e.g., "mobily", "aramco") |
| "Zero results consistently" | Engine file might have syntax error - check logs |

### 6. Enable Debug Logging

Edit `container/settings.template.yml`:

```yaml
logging:
  level: DEBUG
```

Or set environment variable:

```bash
export LOGLEVEL=DEBUG
```

### 7. Manual Engine Test

To manually test the engine logic without SearXNG:

```bash
python3 -c "
import json
from pathlib import Path

# Load domains
db_path = Path('data/domains/saudi_domains.json')
with open(db_path) as f:
    data = json.load(f)

saudi_domains = set(data['saudi_domains'])

# Test query
query = 'mobily'
matches = [d for d in saudi_domains if query in d]
print(f'Query \"{query}\" found {len(matches)} matches')
for m in matches[:5]:
    print(f'  - {m}')
"
```

### 8. Archive Engines Testing

Archive engines are disabled by default for Render free tier (5GB/month bandwidth).

To enable and test:

```bash
# Edit settings.template.yml
# Change 'disabled: true' to 'disabled: false' for any archive engine

# Then test
curl "http://localhost:8080/search?q=wikipedia&engines=wayback_machine&format=json"
```

## Architecture

### Saudi Companies Engine (offline)
- **Type**: Offline/Local search
- **Data**: `data/domains/saudi_domains.json` (3,605 domains)
- **Company Mappings**: `data/domains/company_mappings.json` (10 major companies)
- **No external API calls** - Works completely offline
- **Response time**: < 100ms

### Archive Engines (online)
- **Wayback Machine**: 700B+ archived pages
- **Common Crawl**: 80B+ web crawl data
- **Memento Archive**: Federated time travel API
- **Archive.today**: Permanent preservation
- **Perma.cc**: Academic citations
- **Arquivo.pt**: Portuguese web (5B+ pages)
- **UK Web Archive**: UK domain focus
- **Library of Congress**: US cultural heritage

All disabled by default on Render free tier.

## Performance Metrics

Expected response times:

| Engine | Enabled | Time | Notes |
|--------|---------|------|-------|
| Saudi Companies | ✓ | <100ms | Local lookup, no network |
| Wayback Machine | ✗ | 1-3s | Archive API queries |
| Common Crawl | ✗ | 2-4s | Metadata parsing |
| Memento Archive | ✗ | 3-5s | Federated search |
| Others | ✗ | 1-2s | Direct API calls |

## Troubleshooting Checklist

- [ ] Data files exist and are readable
- [ ] Engine Python files have correct syntax
- [ ] Settings configuration references engines correctly
- [ ] Engine is not disabled in settings
- [ ] Server logs show no import errors
- [ ] Test queries match domain keywords
- [ ] Browser cache is cleared (if testing UI)

## Getting Help

1. Check server logs for specific error messages
2. Run diagnostic tests: `python3 scripts/test_engines_direct.py`
3. Verify data: `ls -lh data/domains/`
4. Test API directly: `curl http://localhost:8080/search?q=test&format=json`
