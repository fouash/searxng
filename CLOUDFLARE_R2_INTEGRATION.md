# Cloudflare R2 Integration for SearXNG

**Purpose:** Use Cloudflare R2 for persistent storage of stats, archives, and backups

**Benefits:**
- ✅ S3-compatible API
- ✅ Pay-as-you-go ($0.015/GB storage, $0.04/GB egress)
- ✅ Unlimited requests (no rate limiting)
- ✅ Survives Render restarts
- ✅ Global CDN (if using custom domain)

---

## Step 1: Get Cloudflare R2 API Key

### Create R2 API Token

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Create Token → Custom token
3. Permissions:
   ```
   Account: Cloudflare R2: Edit
   Zone: None
   TTL: 1 year
   ```
4. Copy credentials:
   - **Access Key ID** (like AWS Access Key)
   - **Secret Access Key** (like AWS Secret Key)

### Create R2 Bucket

1. Go to: https://dash.cloudflare.com/
2. R2 → Create bucket
3. Name: `searxng` (or your choice)
4. Region: Auto
5. Settings → Default → Copy endpoint URL

**Your R2 Credentials:**
```
Bucket name: searxng
Endpoint URL: https://[account-id].r2.cloudflarestorage.com
Access Key ID: [your-key-id]
Secret Access Key: [your-secret]
```

---

## Step 2: Configure SearXNG with R2

### Add Environment Variables

**Create `.env` file in Render:**

```bash
# Cloudflare R2 Configuration
CLOUDFLARE_R2_ACCESS_KEY_ID=your_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_secret_access_key
CLOUDFLARE_R2_BUCKET_NAME=searxng
CLOUDFLARE_R2_ENDPOINT_URL=https://[account-id].r2.cloudflarestorage.com
```

### Update `render.yaml`

```yaml
services:
  - type: web
    name: searxng
    env: docker
    
    envVars:
      - key: CLOUDFLARE_R2_ACCESS_KEY_ID
        sync: false
        value: <your-access-key>
      
      - key: CLOUDFLARE_R2_SECRET_ACCESS_KEY
        sync: false
        value: <your-secret-key>
      
      - key: CLOUDFLARE_R2_BUCKET_NAME
        value: searxng
      
      - key: CLOUDFLARE_R2_ENDPOINT_URL
        value: https://[account-id].r2.cloudflarestorage.com
```

---

## Step 3: Create SearXNG R2 Storage Module

### R2 Storage Client

```python
# searx/storage/r2_storage.py

import os
import boto3
import json
from datetime import datetime
from io import BytesIO

class R2Storage:
    """Cloudflare R2 storage backend"""
    
    def __init__(self):
        self.access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID')
        self.secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.environ.get('CLOUDFLARE_R2_BUCKET_NAME', 'searxng')
        self.endpoint_url = os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL')
        
        if not all([self.access_key, self.secret_key, self.endpoint_url]):
            raise ValueError("Cloudflare R2 credentials not configured")
        
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='auto'
        )
    
    def create_folders(self):
        """Create folder structure in R2"""
        
        folders = [
            'stats/',
            'stats/daily/',
            'stats/monthly/',
            'stats/yearly/',
            'archive/',
            'archive/pages/',
            'archive/metadata/',
            'archive/index/',
            'backups/',
            'backups/database/',
            'backups/config/',
            'logs/',
        ]
        
        for folder in folders:
            # R2 is keyspace-based; create marker files
            try:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder + '.keep',
                    Body=b'',
                    ContentType='application/octet-stream'
                )
                print(f"✓ Created folder: {folder}")
            except Exception as e:
                print(f"✗ Error creating folder {folder}: {e}")
    
    def save_stats(self, stats_data, timestamp=None):
        """Save stats snapshot to R2"""
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Format: stats/daily/2024-01-15/10-30-45.json
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H-%M-%S')
        
        key = f"stats/daily/{date_str}/{time_str}.json"
        
        data = {
            'timestamp': timestamp.isoformat(),
            'stats': stats_data
        }
        
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        
        print(f"✓ Saved stats: {key}")
        return key
    
    def save_archive_page(self, url, html_content, metadata=None):
        """Save archived page to R2"""
        
        import gzip
        import hashlib
        
        timestamp = datetime.utcnow()
        
        # Generate key: archive/pages/2024/01/15/[hash].html.gz
        hash_val = hashlib.md5(url.encode()).hexdigest()
        date_path = timestamp.strftime('%Y/%m/%d')
        key = f"archive/pages/{date_path}/{hash_val}.html.gz"
        
        # Compress
        compressed = gzip.compress(html_content.encode('utf-8'))
        
        # Save page
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=compressed,
            ContentType='text/html',
            ContentEncoding='gzip',
            Metadata={
                'original-url': url,
                'archived-timestamp': timestamp.isoformat()
            }
        )
        
        # Save metadata
        meta_key = f"archive/metadata/{date_path}/{hash_val}.json"
        meta = {
            'url': url,
            'archived': timestamp.isoformat(),
            'size': len(html_content),
            'compressed_size': len(compressed),
            'storage_key': key,
            **(metadata or {})
        }
        
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=meta_key,
            Body=json.dumps(meta).encode('utf-8'),
            ContentType='application/json'
        )
        
        print(f"✓ Archived page: {key}")
        return key
    
    def get_daily_stats(self, date_str):
        """Retrieve all stats for a day (YYYY-MM-DD)"""
        
        prefix = f"stats/daily/{date_str}/"
        
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        
        stats = []
        for obj in response.get('Contents', []):
            resp = self.client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
            data = json.loads(resp['Body'].read())
            stats.append(data)
        
        return sorted(stats, key=lambda x: x['timestamp'])
    
    def get_monthly_stats(self, year_month):
        """Retrieve stats for a month (YYYY-MM)"""
        
        prefix = f"stats/daily/{year_month}/"
        
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        
        all_stats = []
        for obj in response.get('Contents', []):
            resp = self.client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
            data = json.loads(resp['Body'].read())
            all_stats.append(data)
        
        return all_stats
    
    def get_archive_page(self, hash_val):
        """Retrieve archived page"""
        
        import gzip
        
        # Find the key (search all dates)
        prefix = f"archive/pages/"
        
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        
        for obj in response.get('Contents', []):
            if hash_val in obj['Key']:
                resp = self.client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                compressed = resp['Body'].read()
                return gzip.decompress(compressed).decode('utf-8')
        
        return None
    
    def backup_database(self, db_path):
        """Backup SQLite database to R2"""
        
        import shutil
        
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H-%M-%S')
        
        key = f"backups/database/{date_str}/stats_{time_str}.db"
        
        # Read and upload
        with open(db_path, 'rb') as f:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=f.read(),
                ContentType='application/octet-stream'
            )
        
        print(f"✓ Database backup: {key}")
        return key
    
    def list_all_stats(self):
        """List all stats snapshots"""
        
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix='stats/daily/'
        )
        
        return [obj['Key'] for obj in response.get('Contents', [])]
    
    def get_storage_stats(self):
        """Get R2 usage statistics"""
        
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name
        )
        
        total_size = 0
        total_objects = 0
        
        for obj in response.get('Contents', []):
            total_size += obj['Size']
            total_objects += 1
        
        return {
            'total_objects': total_objects,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
        }
```

---

## Step 4: Integrate with SearXNG Stats

### Update Stats Exporter

```python
# searx/stats/exporter.py

from searx.storage.r2_storage import R2Storage

class StatsExporter:
    """Export stats to R2"""
    
    def __init__(self):
        self.r2 = R2Storage()
    
    def export_stats(self, stats_data):
        """Save stats to R2"""
        
        timestamp = datetime.utcnow()
        
        # Save to R2
        key = self.r2.save_stats(stats_data, timestamp)
        
        # Also save to git (backup)
        self._git_backup(stats_data, timestamp)
        
        return key
    
    def _git_backup(self, stats_data, timestamp):
        """Backup to git as well"""
        # Use previous git exporter logic
        pass
```

### Add Export Endpoints

```python
# searx/views/stats.py

@app.route('/stats/r2/list')
def list_r2_stats():
    """List all stats in R2"""
    
    from searx.storage.r2_storage import R2Storage
    r2 = R2Storage()
    
    stats_files = r2.list_all_stats()
    usage = r2.get_storage_stats()
    
    return jsonify({
        'stats_count': len(stats_files),
        'storage_usage': usage,
        'files': stats_files[:100]  # Last 100
    })

@app.route('/stats/r2/usage')
def r2_usage():
    """Show R2 storage usage"""
    
    from searx.storage.r2_storage import R2Storage
    r2 = R2Storage()
    
    usage = r2.get_storage_stats()
    
    return jsonify({
        'total_objects': usage['total_objects'],
        'total_size_mb': usage['total_size_mb'],
        'total_size_gb': usage['total_size_gb'],
        'estimated_monthly_cost': usage['total_size_gb'] * 0.015
    })

@app.route('/stats/backup/r2')
def backup_to_r2():
    """Manually trigger R2 backup"""
    
    from searx.storage.r2_storage import R2Storage
    import sqlite3
    
    r2 = R2Storage()
    
    # Backup database
    db_path = '/usr/local/searxng/data/stats.db'
    key = r2.backup_database(db_path)
    
    return jsonify({
        'status': 'backed_up',
        'key': key
    })
```

---

## Step 5: Create Folder Structure

### Initialize R2

```python
# scripts/init_r2.py

from searx.storage.r2_storage import R2Storage

if __name__ == '__main__':
    r2 = R2Storage()
    print("Creating folder structure in Cloudflare R2...")
    r2.create_folders()
    print("✓ Folder structure created")
    
    # Show current usage
    stats = r2.get_storage_stats()
    print(f"\nR2 Storage Usage:")
    print(f"  Total objects: {stats['total_objects']}")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")
    print(f"  Estimated cost: ${stats['total_size_gb'] * 0.015:.2f}/month")
```

### Run Initialization

```bash
# SSH into Render
render exec -s searxng

# Initialize R2
cd /usr/local/searxng
python3 scripts/init_r2.py

# Output:
# ✓ Created folder: stats/
# ✓ Created folder: stats/daily/
# ✓ Created folder: archive/
# ✓ Folder structure created
```

---

## Step 6: Auto-Export to R2

### Update Startup Script

```bash
# container/render-entrypoint.sh

# ... existing code ...

# Auto-export stats to R2 every 30 minutes
echo "[searxng] Starting R2 stats export daemon..."
(
    while true; do
        sleep 1800  # 30 minutes
        python3 << 'PYTHON_SCRIPT'
from searx.stats.exporter import StatsExporter
from searx.stats import get_search_stats

exporter = StatsExporter()
stats = get_search_stats()
key = exporter.export_stats(stats)
print(f"[searxng] Exported stats to R2: {key}")
PYTHON_SCRIPT
    done
) >> /var/log/searxng-r2-export.log 2>&1 &

exec /usr/local/searxng/entrypoint.sh
```

---

## R2 Folder Structure

After initialization, your R2 will have:

```
searxng/
├── stats/
│   ├── daily/
│   │   ├── 2024-01-15/
│   │   │   ├── 10-30-45.json
│   │   │   ├── 11-00-45.json
│   │   │   └── ...
│   │   └── 2024-01-16/
│   ├── monthly/
│   └── yearly/
│
├── archive/
│   ├── pages/
│   │   ├── 2024/01/15/
│   │   │   ├── [hash1].html.gz
│   │   │   ├── [hash2].html.gz
│   │   │   └── ...
│   │   └── ...
│   ├── metadata/
│   │   └── 2024/01/15/
│   │       ├── [hash1].json
│   │       └── ...
│   └── index/
│
├── backups/
│   ├── database/
│   │   ├── 2024-01-15/
│   │   │   └── stats_10-30-45.db
│   │   └── ...
│   └── config/
│
└── logs/
```

---

## Usage & Monitoring

### Check Storage Usage

```bash
curl https://searxng-e6ur.onrender.com/stats/r2/usage

# Output:
{
  "total_objects": 1452,
  "total_size_mb": 124.5,
  "total_size_gb": 0.1245,
  "estimated_monthly_cost": 0.0019
}
```

### List All Stats

```bash
curl https://searxng-e6ur.onrender.com/stats/r2/list | head -50
```

### Manual Backup

```bash
curl https://searxng-e6ur.onrender.com/stats/backup/r2

# Output:
{
  "status": "backed_up",
  "key": "backups/database/2024-01-15/stats_10-30-45.db"
}
```

---

## Cloudflare R2 Console

### Monitor in Dashboard

1. Go to: https://dash.cloudflare.com/
2. R2 → searxng bucket
3. View:
   - Total objects
   - Total storage used
   - Bandwidth usage
   - Cost tracking

### Estimated Costs

```
Usage scenario:
  Stats: 2.4 MB/day = 72 MB/month
  Archive: 10 GB/month (1B pages)
  Backups: 100 MB/month
  Total: ~10.2 GB/month

Costs:
  Storage: 10.2 GB × $0.015 = $0.153/month
  Bandwidth: Minimal (mostly internal)
  API calls: Unlimited
  
Monthly: ~$0.15-0.25/month
Annual: ~$2-3/year
```

---

## Summary

| Component | Details |
|-----------|---------|
| **Bucket** | searxng |
| **Storage** | Stats + Archives + Backups |
| **Cost** | ~$0.15-0.25/month |
| **Retention** | Permanent |
| **Redundancy** | Automatic (Cloudflare) |
| **Access** | S3-compatible API |

**Status:** ✅ Ready to deploy
**Next:** Deploy and test R2 integration

---

## Quick Deployment Checklist

- [ ] Copy R2 credentials
- [ ] Set environment variables in Render
- [ ] Deploy `r2_storage.py`
- [ ] Deploy `stats/exporter.py` update
- [ ] Deploy `render-entrypoint.sh` update
- [ ] Run `init_r2.py` to create folders
- [ ] Test: `curl /stats/r2/usage`
- [ ] Monitor: Check R2 dashboard

**Once deployed, stats will persist permanently in Cloudflare R2! 🚀**
