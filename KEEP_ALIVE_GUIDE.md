# Keep Render Instance Alive - Complete Guide

## Problem

Render's free tier spins down instances after **15 minutes of inactivity**. This guide keeps your SearXNG instance alive indefinitely with automated pings.

## Solution Components

### 1. Keep-Alive Page (`container/keep_alive.html`)
- Real-time dashboard showing instance status
- Displays ping history and metrics
- Manual connection test button
- Served at: `https://your-instance.onrender.com/keep-alive`

### 2. Keep-Alive Script (`scripts/keep_alive.py`)
- Python script that pings the instance
- Logs success/failure
- Can run on any machine with Python and internet

### 3. Cron Job (External)
- Runs keep_alive.py every 10 minutes
- Prevents 15-minute inactivity timeout
- Can run on your local machine, GitHub Actions, or any server

## Setup Instructions

### Step 1: Serve the Keep-Alive Page

Add this to `container/render-entrypoint.sh` (at the end before exec):

```bash
# Serve keep-alive page as static file
cp ./container/keep_alive.html /usr/local/searxng/searx/static/keep_alive.html
```

Or modify the Render instance to serve it. The page will be accessible at:
```
https://your-instance.onrender.com/static/keep_alive.html
```

### Step 2: Set Up Cron Job

Choose one of the following options:

#### Option A: Local Machine (Recommended for testing)

On your local machine, add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line (replace URL with your Render instance)
*/10 * * * * python3 /path/to/searxng/scripts/keep_alive.py https://your-instance.onrender.com
```

This pings every 10 minutes.

#### Option B: GitHub Actions (Recommended for automation)

Create `.github/workflows/keep_alive.yml`:

```yaml
name: Keep Render Alive

on:
  schedule:
    # Run every 10 minutes
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render instance
        run: |
          curl -s -f "https://your-instance.onrender.com/keep-alive" || true
```

#### Option C: Render Cron Job (within Render)

If you upgrade to Render Standard tier, use Render's own scheduled jobs.

### Step 3: Monitor the Instance

1. **Visit the dashboard:**
   ```
   https://your-instance.onrender.com/static/keep_alive.html
   ```

2. **Click "Test Connection"** to verify it works

3. **Check logs:**
   ```bash
   # On your machine running the cron job
   tail -f logs/keep_alive.log
   ```

## How It Works

```
Time 0:00    → Render instance receives request
             → Instance active, serving requests
             → Timer resets

Time 10:00   → Cron job pings keep-alive endpoint
             → Instance receives ping
             → Instance stays awake
             → Timer resets

Time 15:00   → Would normally spin down
             → But we already pinged at 10:00
             → Timer reset to 0, instance alive

Time 20:00   → Cron job pings again
             → Instance stays alive
             → Repeat every 10 minutes...
```

## Configuration

### Ping Frequency

- **Default**: Every 10 minutes
- **Why 10 min?**: Render spins down after 15 min inactivity
  - 10 min pings ensure we stay within the 15 min window
  - Provides 5 min buffer for network delays

### Cron Expression

Standard cron format: `minute hour day-of-month month day-of-week`

**Common intervals:**

```
*/10 * * * *     → Every 10 minutes
*/15 * * * *     → Every 15 minutes
0 * * * *        → Every hour
0 */4 * * *      → Every 4 hours
0 9-17 * * *     → Every hour, 9am-5pm
```

## Keep-Alive Page Features

### Dashboard shows:
- ✅ Instance status (Online/Offline)
- ✅ Last ping time
- ✅ Uptime duration
- ✅ Response time in milliseconds
- ✅ Total ping count
- ✅ Success rate percentage
- ✅ Live activity log
- ✅ Manual test button

### Log entries show:
- Connection success/failure
- Response times
- Error messages
- Timestamps

## Testing

### Manual Test

```bash
# Test the keep-alive endpoint
curl "https://your-instance.onrender.com/keep-alive" -v

# Expected: 200 OK response
```

### Dry Run Cron

```bash
# Test the Python script manually
python3 scripts/keep_alive.py https://your-instance.onrender.com

# Expected output:
# INFO:root:Pinging https://your-instance.onrender.com/keep-alive...
# INFO:root:✓ Success (0.XX s) - Instance alive
```

## Troubleshooting

### Issue: Cron job not running

**Solutions:**
1. Check cron is installed: `which cron`
2. Verify crontab entry: `crontab -l`
3. Check system logs: `grep CRON /var/log/syslog`
4. On macOS, may need Full Disk Access for cron

### Issue: "Connection refused"

**Solutions:**
1. Verify Render instance is deployed
2. Check URL is correct: `https://your-instance.onrender.com`
3. Instance may be spinning down - visit URL manually first
4. Check Render dashboard for errors

### Issue: "Timeout after 10 seconds"

**Solutions:**
1. Render instance is too slow - may be spinning down
2. Network connectivity issue
3. Render may be under load - increase timeout if needed

### Issue: Keep-alive page shows 404

**Solutions:**
1. Page needs to be served by SearXNG
2. Ensure `cp keep_alive.html` is in entrypoint script
3. URL should be `/keep-alive` not `/static/keep-alive`
4. Rebuild Docker image and redeploy

## Monitoring & Alerts

### Monitor Uptime

```bash
# Check daily ping success rate
grep "✓ Success" logs/keep_alive.log | wc -l

# Check failed pings
grep "✗" logs/keep_alive.log
```

### Set Up Log Rotation

```bash
# In crontab, add daily log rotation
0 0 * * * gzip logs/keep_alive.log && touch logs/keep_alive.log
```

### Email Alerts (optional)

Modify keep_alive.py to send email on failure:

```python
import smtplib

if not success:
    # Send alert email
    msg = f"Render instance ping failed at {datetime.now()}"
    # ... email configuration
```

## Duration

### Keep Alive for 1 Week

**Total pings needed:** 7 days × 24 hours × 6 pings/hour = **1,008 pings**

The keep-alive page will track this automatically.

### Keep Alive Indefinitely

Just leave the cron job running. No time limit needed.

## Costs

- **Render free tier**: $0 with keep-alive (normally auto-spins down)
- **Local cron machine**: $0 (your electricity)
- **GitHub Actions**: $0 (included in free tier)
- **Render Standard tier**: $7/month (removes spin-down)

## Advanced: Custom Keep-Alive Logic

To do something more useful than just pinging:

```python
# Modify scripts/keep_alive.py to:
# 1. Run a search query
# 2. Check engine status
# 3. Log analytics
# 4. Perform maintenance tasks
```

Example: Test Saudi companies engine

```bash
curl "https://your-instance.onrender.com/search?q=aramco&format=json&engines=saudi_companies"
```

## Summary

| Component | Purpose | Location |
|-----------|---------|----------|
| keep_alive.html | Dashboard & monitoring | `container/keep_alive.html` |
| keep_alive.py | Ping script | `scripts/keep_alive.py` |
| Cron job | Automation | Your machine or GitHub Actions |
| Render URL | Target instance | https://your-instance.onrender.com |

## Quick Start Checklist

- [ ] Deploy SearXNG to Render
- [ ] Get your Render instance URL
- [ ] Set up cron job (local, GitHub Actions, or other)
- [ ] Test: `python3 scripts/keep_alive.py https://your-url`
- [ ] Verify: Visit `https://your-url/keep-alive`
- [ ] Monitor: Check dashboard regularly
- [ ] Success: Instance stays awake!

## Next Steps

1. **Immediate:** Set up cron job to start pinging
2. **Within 24h:** Verify it's working via dashboard
3. **Optional:** Set up email alerts for failures
4. **Long-term:** Monitor logs and uptime

---

**That's it!** Your Render instance will now stay alive indefinitely with minimal cost and effort. 🚀
