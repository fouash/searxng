# Save SearXNG Stats Across Render Restarts

**Problem:** Render free tier restarts containers frequently, losing all stats data

**Solution:** Persist stats to external storage that survives restarts

---

## Option 1: Git-Based Persistence (Simplest)

Save stats as JSON commits to git repository.

### Implementation

#### Step 1: Create Stats Exporter

```python
# searx/stats/exporter.py

import json
import subprocess
from datetime import datetime
from pathlib import Path

class StatsGitExporter:
    """Export stats to git for persistence"""
    
    def __init__(self, repo_path='/usr/local/searxng', stats_dir='stats-history'):
        self.repo_path = repo_path
        self.stats_dir = Path(repo_path) / stats_dir
        self.stats_dir.mkdir(exist_ok=True)
    
    def export_stats(self, stats_data):
        """Export stats to git-tracked file"""
        
        # Create dated file
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        file_path = self.stats_dir / f"stats_{date_str}.json"
        
        # Read existing stats for this day
        if file_path.exists():
            with open(file_path, 'r') as f:
                daily_stats = json.load(f)
        else:
            daily_stats = {'snapshots': []}
        
        # Add new snapshot
        snapshot = {
            'timestamp': timestamp.isoformat(),
            'time': time_str,
            'data': stats_data
        }
        daily_stats['snapshots'].append(snapshot)
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(daily_stats, f, indent=2)
        
        # Commit to git
        self._commit_to_git(file_path, date_str)
    
    def _commit_to_git(self, file_path, date_str):
        """Commit stats to git"""
        
        try:
            # Stage file
            subprocess.run(
                ['git', 'add', str(file_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', f"stats: Add snapshots for {date_str}"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Push
            subprocess.run(
                ['git', 'push', '-u', 'origin', 'master'],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                timeout=30
            )
            
            return True
        except Exception as e:
            print(f"Error committing stats: {e}")
            return False
    
    def get_historical_stats(self):
        """Retrieve all historical stats"""
        
        all_stats = {}
        
        for stats_file in sorted(self.stats_dir.glob('stats_*.json')):
            with open(stats_file, 'r') as f:
                all_stats[stats_file.stem] = json.load(f)
        
        return all_stats
```

#### Step 2: Add Export Endpoint

```python
# searx/views/stats.py

from flask import Blueprint, jsonify, render_template
from searx.stats.exporter import StatsGitExporter

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')
exporter = StatsGitExporter()

@stats_bp.route('/searches')
def searches(format=None):
    """Display search stats"""
    
    # Get current stats from searx
    current_stats = get_search_stats()
    
    if request.args.get('format') == 'json':
        return jsonify(current_stats)
    
    # Export to git (persist)
    exporter.export_stats(current_stats)
    
    # Render HTML
    return render_template('stats_searches.html', stats=current_stats)

@stats_bp.route('/history')
def history():
    """View historical stats (restored from git)"""
    
    historical = exporter.get_historical_stats()
    return render_template('stats_history.html', history=historical)

@stats_bp.route('/export')
def export():
    """Export stats as JSON"""
    
    current_stats = get_search_stats()
    exporter.export_stats(current_stats)
    return jsonify({'status': 'exported', 'data': current_stats})
```

#### Step 3: Configure Auto-Export

```bash
# container/render-entrypoint.sh

# ... existing code ...

# Add periodic stats export (every 30 minutes)
echo "Starting stats export daemon..."
(
    while true; do
        sleep 1800  # 30 minutes
        python3 -c "
from searx.stats.exporter import StatsGitExporter
from searx.stats import get_search_stats
exporter = StatsGitExporter()
stats = get_search_stats()
exporter.export_stats(stats)
print('Stats exported to git')
" 2>&1 | tee -a /var/log/searxng-stats.log
    done
) &

exec /usr/local/searxng/entrypoint.sh
```

### Cost & Storage

```
Stats per snapshot (JSON): ~50 KB
Snapshots per day: 48 (every 30 min)
Daily stats: 2.4 MB
Monthly stats: 72 MB
Yearly stats: 900 MB

Git storage: Minimal (excellent compression)
Render: Free (git is included)
Data retention: Permanent (in git history)
```

### Advantages

✅ Free (uses git)
✅ Permanent (git history)
✅ No external services
✅ Version tracking (see changes over time)
✅ Easy to retrieve (JSON files)

### Limitations

❌ ~30 MB/month overhead
❌ Network-dependent (requires git push)
❌ Latency (network round trip)

---

## Option 2: Render Disk Persistence

Save stats to mounted volume (if using paid tier).

```yaml
# render.yaml

services:
  - type: web
    name: searxng
    env: docker
    region: oregon
    plan: standard  # Requires paid tier
    
    # Persistent disk
    disk:
      name: searxng-stats
      mountPath: /data/stats
      sizeGB: 50  # 50 GB for stats
    
    envVars:
      - key: SEARXNG_STATS_DIR
        value: /data/stats
```

**Note:** Only available on Standard+ tiers ($7/month+)

---

## Option 3: SQLite Database (Local)

Store stats in SQLite with git sync.

```python
# searx/stats/db.py

import sqlite3
from datetime import datetime
from pathlib import Path

class StatsDatabase:
    """Store stats in SQLite"""
    
    def __init__(self, db_path='/usr/local/searxng/data/stats.db'):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    search_query TEXT,
                    engine TEXT,
                    result_count INTEGER,
                    response_time_ms FLOAT,
                    success BOOLEAN
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS engine_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    engine TEXT,
                    avg_response_time_ms FLOAT,
                    success_rate FLOAT,
                    total_queries INTEGER
                )
            """)
            
            conn.commit()
    
    def record_search(self, query, engine, result_count, response_time, success):
        """Record a search"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO search_stats
                (search_query, engine, result_count, response_time_ms, success)
                VALUES (?, ?, ?, ?, ?)
            """, (query, engine, result_count, response_time, success))
            conn.commit()
    
    def record_engine_stats(self, engine, avg_time, success_rate, total):
        """Record engine statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO engine_stats
                (engine, avg_response_time_ms, success_rate, total_queries)
                VALUES (?, ?, ?, ?)
            """, (engine, avg_time, success_rate, total))
            conn.commit()
    
    def get_stats_for_date(self, date):
        """Retrieve stats for specific date"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM search_stats
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (date,))
            return cursor.fetchall()
    
    def export_to_json(self, output_path):
        """Export database to JSON"""
        
        import json
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM search_stats ORDER BY timestamp DESC")
            search_stats = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM engine_stats ORDER BY timestamp DESC")
            engine_stats = [dict(row) for row in cursor.fetchall()]
        
        with open(output_path, 'w') as f:
            json.dump({
                'search_stats': search_stats,
                'engine_stats': engine_stats,
                'export_date': datetime.utcnow().isoformat()
            }, f, indent=2)
```

#### Configure Auto-Sync

```bash
# Sync SQLite to git every 6 hours
0 */6 * * * sqlite3 /usr/local/searxng/data/stats.db ".backup /tmp/stats-backup.db" && \
  cp /tmp/stats-backup.db /usr/local/searxng/data/stats.db && \
  cd /usr/local/searxng && \
  git add data/stats.db && \
  git commit -m "auto: Backup stats database" && \
  git push origin master
```

---

## Option 4: Cloud Storage (S3/Backblaze)

Store stats on S3-compatible storage (persistent, cheap).

```python
# searx/stats/cloud_storage.py

import boto3
import json
from datetime import datetime

class S3StatsStorage:
    """Store stats on S3"""
    
    def __init__(self, bucket_name, endpoint_url=None):
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url  # For Backblaze B2
        )
        self.bucket = bucket_name
    
    def save_stats(self, stats_data):
        """Save stats to S3"""
        
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        key = f"stats/{date_str}/{time_str}.json"
        
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps({
                'timestamp': timestamp.isoformat(),
                'data': stats_data
            }),
            ContentType='application/json'
        )
    
    def get_daily_stats(self, date):
        """Retrieve all stats for a day"""
        
        prefix = f"stats/{date}/"
        
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix
        )
        
        stats = []
        for obj in response.get('Contents', []):
            resp = self.s3.get_object(Bucket=self.bucket, Key=obj['Key'])
            data = json.loads(resp['Body'].read())
            stats.append(data)
        
        return stats
```

### Cost (Backblaze B2)

```
Storage: $0.006 per GB/month
Bandwidth: $0.01 per GB (first 1GB free)

Estimate for 1 year:
  Stats size: ~900 MB
  Cost: ~$5/year storage
  Cost: ~$0 bandwidth (small files)
  Total: ~$5/year
```

### Setup

```bash
# Install boto3
pip install boto3

# Configure credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_ENDPOINT_URL=https://s3.backblazeb2.com

# Use S3StatsStorage in SearXNG
```

---

## Recommended: Hybrid Approach

Combine git + SQLite for best reliability:

```python
# searx/stats/hybrid_storage.py

class HybridStatsStorage:
    """Use both git and SQLite"""
    
    def __init__(self):
        self.git_exporter = StatsGitExporter()
        self.db = StatsDatabase()
    
    def save_stats(self, stats_data):
        """Save to both storage backends"""
        
        # Save to SQLite (fast, local)
        for search in stats_data.get('searches', []):
            self.db.record_search(
                search['query'],
                search['engine'],
                search['result_count'],
                search['response_time'],
                search['success']
            )
        
        # Save to git (permanent backup)
        self.git_exporter.export_stats(stats_data)
    
    def get_stats(self, date):
        """Retrieve from SQLite (fast)"""
        return self.db.get_stats_for_date(date)
    
    def export_backup(self, path):
        """Export to file (for download)"""
        self.db.export_to_json(path)
```

---

## Implementation: Export Current Stats

### Save Stats Right Now

```bash
# SSH into Render container
render exec -s searxng

# Export current stats
python3 << 'EOF'
import json
from datetime import datetime
from pathlib import Path

# Get current stats from SearXNG
import requests
resp = requests.get('http://localhost:8080/stats/searches?format=json')
stats = resp.json()

# Save to file
timestamp = datetime.utcnow().isoformat()
output = {
    'timestamp': timestamp,
    'stats': stats
}

# Save locally
Path('/tmp/stats_export.json').write_text(json.dumps(output, indent=2))

# Also save to git
Path('/usr/local/searxng/stats-history').mkdir(exist_ok=True)
Path('/usr/local/searxng/stats-history/current.json').write_text(
    json.dumps(output, indent=2)
)

print("Stats exported to /tmp/stats_export.json")
print(json.dumps(output, indent=2)[:500])
EOF

# Download the file
curl https://searxng-e6ur.onrender.com/stats/export > stats_backup.json
```

---

## Recommended Solution for Your Setup

**Best for Render free tier:**

```python
# Use Git-Based Persistence

Implementation:
1. Add StatsGitExporter to SearXNG
2. Export stats every 30 minutes
3. Auto-commit and push to git
4. Stats survive restarts

Advantages:
✅ Free (uses git)
✅ Permanent (git history)
✅ Simple implementation
✅ View history anytime

Setup time: 2 hours
Monthly cost: $0
Data retention: Permanent
```

### Quick Implementation

```bash
# 1. Copy stats exporter code
# 2. Add to render-entrypoint.sh:
echo "Starting stats export..." 
(
    while true; do
        sleep 1800  # Every 30 min
        python3 /usr/local/searxng/searx/stats/exporter.py
    done
) &

# 3. Deploy
git push origin master

# 4. View stats
# Current: https://searxng-e6ur.onrender.com/stats/searches
# History: https://searxng-e6ur.onrender.com/stats/history
```

---

## Summary

| Approach | Cost | Setup | Reliability | Best For |
|----------|------|-------|-------------|----------|
| **Git** | Free | 2 hrs | ⭐⭐⭐⭐⭐ | Render free tier |
| **SQLite** | Free | 3 hrs | ⭐⭐⭐⭐ | Local backup |
| **S3** | $5/yr | 1 hr | ⭐⭐⭐⭐⭐ | Permanent cloud |
| **Render disk** | $7+/mo | 1 hr | ⭐⭐⭐⭐⭐ | Requires paid tier |
| **Hybrid** | Free | 4 hrs | ⭐⭐⭐⭐⭐ | Maximum reliability |

**Recommendation:** Start with Git-based (free, simple), upgrade to Hybrid later.
