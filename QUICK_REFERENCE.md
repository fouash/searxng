# SearXNG Quick Reference Card

## Problem: "No Results Found" (عفوا ! لم يتم العثور على نتائج)

### Quick Fix Checklist

```bash
# 1. Validate configuration (1 minute)
python3 scripts/validate_deployment.py

# Expected: "Deployment Status: ✓ READY"

# 2. Test data files (1 minute)
python3 scripts/test_engines_direct.py

# Expected: "✓ Saudi domains: 3605 Saudi + 655 regional"

# 3. If running, test API (2 minutes)
python3 scripts/test_searxng_api.py --query aramco

# Expected: "✓ Found X results"
```

If all pass: **Problem is in how SearXNG is loading/calling the engine**

---

## Issue Resolution Guide

### Issue 1: "Engine not found" Error

**Quick Fix:**
```bash
ls -la searx/engines/saudi_companies_db.py
# Should exist and have content
```

**Solution:**
- Restart container: `docker restart <container>`
- Rebuild image: `docker build -t searxng-render .`

---

### Issue 2: "Database not loaded" Error

**Quick Fix:**
```bash
# Check file exists and is valid
python3 -c "import json; json.load(open('data/domains/saudi_domains.json')); print('✓ Valid JSON')"

# Check size is reasonable (should be ~100KB)
ls -lh data/domains/saudi_domains.json
```

**Solution:**
- Ensure file is in build context: `COPY ./data/ ./data/`
- Rebuild Docker image
- Check file permissions: `chmod 644 data/domains/*.json`

---

### Issue 3: Timeout or Slow Responses

**Quick Fix:**
```bash
# Test engine response time
time curl "http://localhost:8080/search?q=test&format=json" > /dev/null

# Expected: <1 second for Saudi DB
```

**Solution:**
- Archive engines (if enabled) are slow - check which one is enabled
- Disable slow engines: `disabled: true` in settings.yml
- Check Render resource usage (RAM, CPU)

---

### Issue 4: Specific Engine Returns Empty Results

**Quick Fix:**
```bash
# Test single engine
curl "http://localhost:8080/search?q=aramco&engines=saudi_companies&format=json"

# Check status
curl "http://localhost:8080/status" | jq '.engines[] | select(.name=="saudi companies")'
```

**Solution:**
- Check engine is enabled: `disabled: false`
- Restart SearXNG
- Check logs for import errors
- Verify engine file syntax: `python3 -m py_compile searx/engines/saudi_companies_db.py`

---

## Common Queries to Test

| Query | Expected Results | Engine |
|-------|------------------|--------|
| `aramco` | 20-50 matches | Saudi Companies DB |
| `stc` | 10-20 matches | Saudi Companies DB |
| `mobily` | 30-40 matches | Saudi Companies DB |
| `bank` | 50+ matches | Saudi Companies DB |
| `wikipedia` | 700B+ pages available | Wayback Machine (if enabled) |

---

## Test Commands

### Local (No Docker)
```bash
# Test data validity
python3 scripts/test_engines_direct.py

# Validate deployment
python3 scripts/validate_deployment.py
```

### Docker Container
```bash
# Build image
docker build -t searxng-render .

# Run container
docker run -p 8080:8080 searxng-render

# In another terminal
curl "http://localhost:8080/search?q=aramco&format=json"
```

### Render Instance (Live)
```bash
# Get URL from Render dashboard
RENDER_URL="https://your-instance.onrender.com"

# Test search
curl "$RENDER_URL/search?q=aramco&format=json" | jq '.results | length'

# Test specific engine
curl "$RENDER_URL/search?q=mobily&engines=saudi_companies&format=json"

# Get server status
curl "$RENDER_URL/status"
```

---

## Useful Diagnostic Commands

```bash
# Check engine file exists
find . -name "*.py" -path "*/engines/*" | wc -l
# Expected: Should include saudi_companies_db.py

# Verify JSON files
python3 -c "
import json
for f in ['data/domains/saudi_domains.json', 'data/domains/company_mappings.json']:
    try:
        d = json.load(open(f))
        print(f'✓ {f}: Valid')
    except Exception as e:
        print(f'❌ {f}: {e}')
"

# Check Dockerfile syntax
docker build --dry-run -t searxng-render .

# View Render logs
# In Render dashboard: Navigate to service > Logs
```

---

## Render-Specific Issues

| Problem | Check |
|---------|-------|
| "Build failed" | Check Logs tab in Render dashboard |
| "Application crashed" | Check entrypoint script exists and is executable |
| "Cold start slow" | Normal for first start; 10-20 seconds expected |
| "No outbound access" | ✓ Correct for free tier; use offline engines only |
| "5GB/month exceeded" | Archive engines enabled; disable or upgrade to Standard |

---

## Files to Check

| File | Purpose | Typical Size |
|------|---------|--------------|
| `Dockerfile` | Build configuration | ~3 KB |
| `container/settings.template.yml` | Engine config | ~5 KB |
| `container/render-entrypoint.sh` | Startup script | ~4 KB |
| `searx/engines/saudi_companies_db.py` | Engine code | ~8 KB |
| `data/domains/saudi_domains.json` | Domain data | ~114 KB |
| `data/domains/company_mappings.json` | Company mappings | ~3 KB |

---

## When to Restart

| Change | Restart Required |
|--------|-----------------|
| Edit settings.yml | Yes - recreate container or restart |
| Add/modify engine file | Yes - rebuild image |
| Update domain data | Yes - rebuild image or mount volume |
| Change Dockerfile | Yes - rebuild image |
| Simple config in env vars | No - restart container only |

---

## Debug Mode

Enable detailed logging:

**In Docker:**
```bash
docker run -e LOGLEVEL=DEBUG -p 8080:8080 searxng-render
```

**In settings.yml:**
```yaml
logging:
  level: DEBUG
```

**View logs:**
```bash
docker logs -f <container_id>
```

---

## Success Indicators

✓ **When deployment is working:**
- `python3 scripts/validate_deployment.py` → "READY"
- `curl localhost:8080/search?q=aramco&format=json` → Returns results
- Results include title, url, engine fields
- Response time <1 second
- No error messages in logs

✓ **Expected output:**
```json
{
  "results": [
    {
      "title": "domain.com.sa",
      "url": "https://domain.com.sa",
      "content": "Saudi company domain - Found in Certificate Transparency logs",
      "engine": "saudi_companies_db"
    }
  ]
}
```

---

## Emergency Reset

If everything is broken:

```bash
# Clear cache and rebuild
docker system prune -a
docker build --no-cache -t searxng-render .
docker run -p 8080:8080 searxng-render

# Or on Render: delete service and redeploy
# Dashboard > Service Settings > Delete > Redeploy
```

---

## Contact Points for Issues

1. **Validation failed**: Check file existence and JSON syntax
2. **Build failed**: Review Render or Docker build logs
3. **No results**: Run `python3 scripts/validate_deployment.py`
4. **Slow responses**: Check which engines are enabled
5. **Startup errors**: Check `container/render-entrypoint.sh` logic

---

**Last Updated**: 2026-07-23  
**SearXNG Version**: Latest  
**Deployment Target**: Render Free Tier
