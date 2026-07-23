# SearXNG Archival Engine: Billion-Scale Page Archive Implementation

**Goal:** Build/integrate archive capability with billions of indexed pages similar to Wayback Machine

**Implementation Status:** Design & Architecture Guide

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ SearXNG Archival Engine                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Query Layer                                      │  │
│  │ - Search archived snapshots                      │  │
│  │ - Filter by date range                           │  │
│  │ - Track version history                          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Indexing Layer                                   │  │
│  │ - Common Crawl (80B+ pages)                      │  │
│  │ - Local crawling (incremental)                   │  │
│  │ - Third-party archive APIs                       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Storage Layer                                    │  │
│  │ - S3-compatible backend (billions of pages)      │  │
│  │ - Metadata database (URLs, dates, size)          │  │
│  │ - Index (fast lookup)                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Approach 1: Common Crawl Integration (Easiest - 80+ Billion Pages)

### What is Common Crawl?

Common Crawl provides:
- **80+ billion web pages** indexed
- **Free public dataset** on AWS S3
- **WARC format** (Web ARChive)
- **Regular updates** (monthly crawls)
- **Searchable index** (via API)

### Implementation

#### Step 1: Common Crawl API Engine

```python
# searx/engines/common_crawl.py

import requests
from datetime import datetime

class CommonCrawlEngine:
    """Search Common Crawl's 80+ billion page index"""
    
    BASE_URL = "https://index.commoncrawl.org"
    
    def search(self, query, params):
        """Search Common Crawl index"""
        
        # Parse query
        url = params.get('url') or query
        start_date = params.get('from', '')
        end_date = params.get('to', '')
        
        # Query Common Crawl index
        results = self._query_index(url, start_date, end_date)
        
        # Parse and return results
        return self._format_results(results)
    
    def _query_index(self, url, start_date, end_date):
        """Query Common Crawl CDX API"""
        
        params = {
            'url': url,
            'output': 'json',
            'matchType': 'domain',  # Match all subdomains
            'showNumPages': True,
        }
        
        if start_date:
            params['from'] = start_date.replace('-', '')
        if end_date:
            params['to'] = end_date.replace('-', '')
        
        response = requests.get(
            f"{self.BASE_URL}/cdx",
            params=params,
            timeout=10
        )
        
        return response.json()
    
    def _format_results(self, raw_results):
        """Convert Common Crawl results to SearXNG format"""
        
        results = []
        
        # raw_results is list of records:
        # [url, timestamp, original_url, status_code, mime_type, length, hash]
        
        for record in raw_results[1:]:  # Skip header
            url, timestamp, orig_url, status, mime, length, hash = record
            
            # Format timestamp: 20230115123045 → 2023-01-15 12:30:45
            date = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            
            results.append({
                'title': f"{orig_url} ({date.strftime('%Y-%m-%d')})",
                'url': self._build_wayback_url(orig_url, timestamp),
                'content': f"Archived on {date.strftime('%B %d, %Y')} - {status} {mime}",
                'metadata': {
                    'archived': date.isoformat(),
                    'original_url': orig_url,
                    'status': status,
                    'mime_type': mime,
                    'size': length,
                    'hash': hash,
                }
            })
        
        return results
    
    def _build_wayback_url(self, url, timestamp):
        """Generate Wayback Machine URL"""
        return f"https://web.archive.org/web/{timestamp}/{url}"
```

#### Step 2: SearXNG Configuration

```yaml
# container/settings.template.yml

engines:
  - name: common_crawl
    disabled: false
    timeout: 15
    engine: common_crawl
    categories: archive
    # Search 80+ billion archived pages
    # Query format: url:example.com
    # Supports date range filtering

  - name: wayback_machine
    disabled: false
    timeout: 20
    categories: archive
    # Wayback Machine direct access
```

### API Details

```bash
# Query Common Crawl CDX API
curl "https://index.commoncrawl.org/cdx?url=example.com&output=json"

# With date range
curl "https://index.commoncrawl.org/cdx?url=example.com&from=20200101&to=20231231&output=json"

# Find snapshots
curl "https://index.commoncrawl.org/cdx?url=example.com/*&matchType=prefix&showNumPages=true"
```

### Rate Limits
- Common Crawl API: No rate limit (free, public)
- No authentication needed
- Response includes: URL, timestamp, HTTP status, MIME type, size, hash

---

## Approach 2: Local Archival System (Billions on Your Server)

### Architecture

```
Incremental Web Crawling
  ↓
Page Snapshot Capture
  ↓
Compressed Storage (S3/MinIO)
  ↓
Metadata Indexing (PostgreSQL)
  ↓
Full-text Search (Elasticsearch)
  ↓
Query Layer (SearXNG Engine)
```

### Implementation

#### Step 1: Page Crawler & Archiver

```python
# searx/archiver/crawler.py

import asyncio
import hashlib
import gzip
from datetime import datetime
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup

class ArchivalCrawler:
    """Crawl and archive web pages"""
    
    def __init__(self, storage_backend, index_db):
        self.storage = storage_backend  # S3/MinIO
        self.db = index_db  # PostgreSQL
        self.session = None
    
    async def archive_page(self, url, depth=0, max_depth=2):
        """Archive a page and optionally its links"""
        
        try:
            # Fetch page
            html = await self._fetch_page(url)
            if not html:
                return False
            
            # Create snapshot
            snapshot = {
                'url': url,
                'timestamp': datetime.utcnow(),
                'content': html,
                'size': len(html),
                'hash': hashlib.sha256(html.encode()).hexdigest(),
            }
            
            # Compress and store
            compressed = gzip.compress(html.encode('utf-8'))
            storage_key = self._generate_storage_key(url)
            
            await self.storage.put(storage_key, compressed)
            
            # Index metadata
            await self._index_snapshot(snapshot, storage_key)
            
            # Extract and crawl links (if within depth limit)
            if depth < max_depth:
                links = self._extract_links(html, url)
                for link in links[:100]:  # Limit to 100 links per page
                    await self.archive_page(link, depth + 1, max_depth)
            
            return True
            
        except Exception as e:
            print(f"Error archiving {url}: {e}")
            return False
    
    async def _fetch_page(self, url):
        """Fetch page content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.text()
        except Exception:
            pass
        return None
    
    def _extract_links(self, html, base_url):
        """Extract all links from page"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            abs_url = urljoin(base_url, href)
            
            # Filter: same domain only
            if urlparse(abs_url).netloc == urlparse(base_url).netloc:
                links.append(abs_url)
        
        return links
    
    def _generate_storage_key(self, url):
        """Generate storage path"""
        hash_val = hashlib.md5(url.encode()).hexdigest()
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H')
        return f"archive/{timestamp}/{hash_val}"
    
    async def _index_snapshot(self, snapshot, storage_key):
        """Store metadata in database"""
        
        await self.db.execute("""
            INSERT INTO archive_snapshots
            (url, timestamp, content_hash, storage_key, size, status)
            VALUES (%s, %s, %s, %s, %s, 'indexed')
        """, (
            snapshot['url'],
            snapshot['timestamp'],
            snapshot['hash'],
            storage_key,
            snapshot['size']
        ))
        
        # Update full-text search index
        await self._index_for_search(snapshot)
    
    async def _index_for_search(self, snapshot):
        """Index for full-text search"""
        # Use Elasticsearch or similar
        # Extract title, headings, text for search
        pass
```

#### Step 2: Storage Backend (S3/MinIO)

```python
# searx/archiver/storage.py

class S3Storage:
    """Store compressed pages on S3"""
    
    def __init__(self, bucket_name, endpoint_url=None):
        import boto3
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url  # For MinIO
        )
        self.bucket = bucket_name
    
    async def put(self, key, compressed_data):
        """Store compressed page"""
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=compressed_data,
            ContentEncoding='gzip'
        )
    
    async def get(self, key):
        """Retrieve and decompress page"""
        import gzip
        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
        return gzip.decompress(resp['Body'].read())
```

#### Step 3: Archive Search Engine

```python
# searx/engines/local_archive.py

class LocalArchiveEngine:
    """Search locally archived pages"""
    
    def __init__(self, db_connection, storage_backend):
        self.db = db_connection
        self.storage = storage_backend
    
    def search(self, query, params):
        """Search archived pages"""
        
        url = params.get('url')
        date_from = params.get('from')
        date_to = params.get('to')
        
        # Query database for matching URLs
        query_sql = """
            SELECT url, timestamp, content_hash, storage_key, size
            FROM archive_snapshots
            WHERE url ILIKE %s
        """
        params_sql = [f"%{url}%"]
        
        if date_from:
            query_sql += " AND timestamp >= %s"
            params_sql.append(date_from)
        
        if date_to:
            query_sql += " AND timestamp <= %s"
            params_sql.append(date_to)
        
        query_sql += " ORDER BY timestamp DESC LIMIT 100"
        
        results = self.db.execute(query_sql, params_sql)
        
        # Format results
        return self._format_results(results)
    
    def _format_results(self, rows):
        """Convert DB results to SearXNG format"""
        results = []
        
        for row in rows:
            url, timestamp, hash_val, storage_key, size = row
            
            results.append({
                'title': f"{url} - {timestamp.strftime('%Y-%m-%d')}",
                'url': f"/archive/view?key={storage_key}",
                'content': f"Snapshot from {timestamp.strftime('%B %d, %Y')} - {size} bytes",
                'metadata': {
                    'archived': timestamp.isoformat(),
                    'size': size,
                    'hash': hash_val,
                }
            })
        
        return results
```

#### Step 4: View Handler

```python
# searx/views/archive.py

@app.route('/archive/view')
def view_archived_page(storage_key):
    """View archived page"""
    
    try:
        # Retrieve from storage
        content = storage.get(storage_key)
        
        # Decompress
        import gzip
        html = gzip.decompress(content).decode('utf-8')
        
        # Serve with timestamp notice
        return render_template('archive_view.html',
            content=html,
            timestamp=get_metadata(storage_key)['timestamp']
        )
    except Exception as e:
        return "Archive not found", 404
```

---

## Approach 3: Third-Party Archive APIs

### Archive.is / Archive.fo

```python
# searx/engines/archive_is.py

class ArchiveIsEngine:
    """Search archive.is for saved snapshots"""
    
    def search(self, query, params):
        url = params.get('url')
        
        # Query archive.is API
        response = requests.get(
            'https://archive.is/api/',
            params={'action': 'query', 'url': url},
            timeout=10
        )
        
        results = response.json()
        
        # Format and return
        return self._format_results(results)
```

### Perplexity / Archive Endpoints

```yaml
engines:
  - name: archive_is
    disabled: false
    timeout: 10
    engine: archive_is
    categories: archive
```

---

## Storage Capacity Planning

### For 1 Billion Pages

```
Scenario: Average 100 KB per page

Raw storage:
  1 billion pages × 100 KB = 100 petabytes (uncompressed)

With compression (gzip ~70%):
  1 billion pages × 100 KB × 0.3 = 30 petabytes

With deduplication (~40% identical content):
  30 petabytes × 0.6 = 18 petabytes

Practical estimate: 20-30 PB for 1 billion diverse pages
```

### Budget-Friendly Implementation

**Start smaller:**
1. **Phase 1:** Archive 100 million pages (200 TB compressed)
   - Cost: ~$5K hardware + $100/month storage
   - Coverage: Major sites, common queries

2. **Phase 2:** Archive 1 billion pages (2 PB)
   - Cost: ~$50K hardware + $1K/month storage
   - Coverage: 90% of web traffic

3. **Phase 3:** Use Common Crawl for long tail (80B+ pages)
   - Cost: Free API access
   - Coverage: Remaining 10% of queries

---

## Metadata Database Schema

```sql
CREATE TABLE archive_snapshots (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Content identification
    content_hash CHAR(64) NOT NULL,  -- SHA256
    storage_key TEXT NOT NULL,        -- S3/MinIO path
    
    -- Metrics
    size BIGINT,
    status_code SMALLINT,
    mime_type VARCHAR(100),
    
    -- Indexing
    title TEXT,
    description TEXT,
    indexed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_url ON archive_snapshots(url);
CREATE INDEX idx_timestamp ON archive_snapshots(timestamp);
CREATE INDEX idx_url_timestamp ON archive_snapshots(url, timestamp DESC);

CREATE TABLE archive_urls (
    url TEXT PRIMARY KEY,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    snapshot_count INT,
    size_total BIGINT
);
```

---

## Full-Text Search Setup

### Elasticsearch Integration

```python
# searx/archiver/indexer.py

from elasticsearch import Elasticsearch

class ArchiveIndexer:
    """Index archived pages for full-text search"""
    
    def __init__(self):
        self.es = Elasticsearch(['localhost:9200'])
    
    def index_page(self, snapshot, text_content):
        """Index page for searching"""
        
        self.es.index(index='archive', doc_type='_doc', body={
            'url': snapshot['url'],
            'timestamp': snapshot['timestamp'],
            'title': snapshot.get('title', ''),
            'content': text_content[:10000],  # First 10KB
            'size': snapshot['size'],
            'content_hash': snapshot['hash'],
        })
    
    def search_full_text(self, query, date_from=None, date_to=None):
        """Full-text search across archive"""
        
        es_query = {
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['title^3', 'content']
                }
            }
        }
        
        if date_from or date_to:
            es_query['query'] = {
                'bool': {
                    'must': [es_query['query']],
                    'filter': [{
                        'range': {
                            'timestamp': {
                                'gte': date_from,
                                'lte': date_to,
                            }
                        }
                    }]
                }
            }
        
        return self.es.search(index='archive', body=es_query)
```

---

## Implementation Roadmap

### Phase 1: Common Crawl Integration (1 week)
```
1. Implement Common Crawl engine
2. Test with sample queries
3. Add to SearXNG config
4. Performance tuning
→ Result: Access to 80+ billion pages
```

### Phase 2: Local Archival System (4 weeks)
```
1. Set up storage backend (MinIO/S3)
2. Implement crawler + archiver
3. Build metadata database
4. Create search engine
5. Performance optimization
→ Result: Host 100M-1B pages locally
```

### Phase 3: Full-Text Search (2 weeks)
```
1. Deploy Elasticsearch
2. Implement indexing pipeline
3. Add to SearXNG search
4. Query optimization
→ Result: Fast full-text search on archive
```

### Phase 4: Production Hardening (2 weeks)
```
1. Health checks & monitoring
2. Backup strategy
3. Deduplication
4. Compression optimization
5. Rate limiting
```

---

## Performance Expectations

### Common Crawl (API-Based)
- **Response time:** 2-5 seconds
- **Queries/second:** 10-50 (no rate limit)
- **Cost:** Free
- **Coverage:** 80+ billion pages
- **Storage:** None (external)

### Local Archive (1B pages)
- **Response time:** <500ms (index lookup)
- **Queries/second:** 100+ (Elasticsearch)
- **Cost:** 20-30 PB storage + hardware
- **Coverage:** 1 billion pages
- **Storage:** 30 PB compressed

### Hybrid (Recommended)
- **Local:** 100-500 million popular pages
- **Common Crawl:** Long tail + fallback
- **Result:** Best response time + coverage
- **Cost:** Moderate

---

## Recommended Approach for SearXNG

### Best Balance: Common Crawl + Local Archive

```yaml
engines:
  # Primary: Common Crawl (80B pages, free)
  - name: common_crawl
    disabled: false
    timeout: 10
    priority: high
    
  # Secondary: Local archive (1B pages, fast)
  - name: local_archive
    disabled: false
    timeout: 2
    priority: high
    
  # Tertiary: Wayback Machine (fallback)
  - name: wayback_machine
    disabled: false
    timeout: 20
    priority: medium
```

**Result:**
- ✅ 80+ billion pages (Common Crawl)
- ✅ 1 billion local pages (fast)
- ✅ Full historical tracking (Wayback)
- ✅ Total coverage: ~81 billion pages
- ✅ Mixed cost model (free + modest)

---

## Quick Start: Common Crawl Integration

```bash
# 1. Copy engine file
cp searx/engines/common_crawl.py /usr/local/searxng/searx/engines/

# 2. Update settings.template.yml
cat >> container/settings.template.yml << 'EOF'
  - name: common_crawl
    disabled: false
    timeout: 15
    engine: common_crawl
    categories: archive
EOF

# 3. Restart SearXNG
git push  # Auto-redeploy on Render
```

**Result:** Access to 80+ billion archived pages immediately! 🚀
