# Internet Archive & Historical Web Integration for SearXNG

**Purpose:** Integrate multiple historical web archives into SearXNG for comprehensive historical search coverage.

**Scope:** Wayback Machine, Common Crawl, regional archives, and specialized preservation services

---

## Archive Sources Overview

### Primary Global Archives

#### 1. Internet Archive (Wayback Machine)
**URL:** https://web.archive.org/
**Coverage:** 700+ billion web pages from 1996-present
**API:** CDX API + Wayback API
**Cost:** Free

```python
# Example: Query Wayback Machine CDX API
# GET https://web.archive.org/cdx/search/cdx?url=example.com&output=json&filter=statuscode:200&collapse=urlkey

# Returns: List of snapshots with timestamps, status codes, MIME types
[
  ["timestamp", "statuscode", "original", "statuscode", "length", "offset", "filename"],
  ["20240101120000", "200", "http://example.com/", "200", "5000", "12345", "example.com-20240101120000.warc.gz"],
  ...
]
```

**Integration Points:**
- Historical page snapshots
- Multiple versions of same page
- Metadata: size, HTTP status, MIME type
- Full-text index search

#### 2. Common Crawl
**URL:** https://commoncrawl.org/
**Coverage:** 80+ billion indexed pages, updated monthly
**Data:** WARC files (raw crawl data) + CDX index
**Cost:** Free (AWS S3, ~$1-2 per crawl query)

```python
# CDX API for searching Common Crawl
# GET https://index.commoncrawl.org/CC-MAIN-2024-10-index?url=example.com&output=json

# Returns crawl snapshots with URLs and WARC file references
{
  "url": "http://example.com/",
  "timestamp": "20240101120000",
  "status_code": "200",
  "filename": "s3://commoncrawl/crawl-data/CC-MAIN-2024-10/segments/.../warc.gz",
  "offset": "12345",
  "length": "5000"
}
```

**Integration Points:**
- Bulk historical snapshots
- WARC file retrieval (can decompress)
- MIME type detection
- Canonical URL detection

#### 3. Memento Time Travel
**URL:** https://timetravel.mementoweb.org/
**Coverage:** Aggregates multiple archives (Wayback, Archive.today, UK Web Archive, etc.)
**API:** Memento Protocol (RFC 7089)
**Cost:** Free

```python
# Memento Protocol: Accept-Datetime header
# GET http://example.com/ with header: Accept-Datetime: Wed, 21 Oct 2024 07:28:00 GMT
# Response: Link header points to archived version

# Or use aggregator directly:
# GET https://timetravel.mementoweb.org/list/json/http://example.com/

# Returns: List of mementos from all available archives
{
  "memento_list": {
    "memento": [
      {
        "datetime": "2024-01-01T12:00:00Z",
        "uri": "https://web.archive.org/web/20240101120000/http://example.com/"
      },
      {
        "datetime": "2024-01-01T13:00:00Z",
        "uri": "https://archive.today/2024-01-01/example.com"
      }
    ]
  }
}
```

---

### Regional Archives

#### 4. Arquivo.pt (Portuguese Web Archive)
**URL:** https://arquivo.pt/
**Coverage:** Portuguese web content (5+ billion pages)
**API:** CDX-compatible API
**Cost:** Free

```bash
# Search: GET https://arquivo.pt/noFrame/wayback/*/example.pt/*?output=json
```

#### 5. UK Web Archive
**URL:** https://www.webarchive.org.uk/
**Coverage:** UK domain content
**API:** OAI-PMH + Search
**Cost:** Free

#### 6. Library of Congress Web Archives
**URL:** https://www.loc.gov/web-archives/
**Coverage:** Selective US government & cultural content
**API:** Search interface (limited programmatic API)
**Cost:** Free

---

### Specialized Services

#### 7. Archive.today / Archive.is
**URL:** https://archive.today/ / https://archive.is/
**Coverage:** Manually archived pages (often used for citation/proof)
**API:** Search interface, direct snapshots
**Cost:** Free

**Features:**
- Permanent link generation
- Screenshot capture
- Redaction capability
- No deletion (permanent preservation)

#### 8. Perma.cc
**URL:** https://perma.cc/
**Coverage:** Academic & legal citations (200+ million links)
**API:** REST API
**Cost:** Free for basic use, institutional licenses available

```bash
# API: GET https://perma.cc/api/v1/captures?url=example.com
# Returns: List of permanent links with metadata
```

#### 9. Webrecorder
**URL:** https://webrecorder.net/
**Coverage:** Web archives + interactive replay
**API:** WARC file retrieval, metadata search
**Cost:** Free community, paid for organizations

---

### Historical Replay Services

#### 10. OldWeb.today
**URL:** https://oldweb.today/
**Features:** Browse archived pages with historical browsers
**Browsers:** IE 5.5, Netscape, Firefox 1.0, Safari 1.0, etc.
**API:** Limited API for snapshots
**Cost:** Free

---

## Implementation Strategy

### Tier 1: Core Archives (High Priority)

These provide broad coverage and reliable APIs:

```
1. Wayback Machine (Internet Archive)
   - 700B pages, proven API, widely trusted
   - Primary for most historical queries

2. Common Crawl
   - 80B pages, monthly updates, structured data
   - Best for bulk historical search

3. Memento Aggregator
   - Federated search across all archives
   - Single API for multi-archive queries
```

### Tier 2: Regional/Specialized (Medium Priority)

These provide coverage gaps:

```
4. Arquivo.pt - Portuguese content
5. UK Web Archive - UK content
6. Archive.today - Permanent preservation
7. Perma.cc - Citation/legal preservation
```

### Tier 3: Replay/Enhanced (Lower Priority)

```
8. Webrecorder - Enhanced archival
9. OldWeb.today - Historical browsing
```

---

## Python Implementation

### Core Archive Engine

```python
# searx/engines/archive_search.py

import httpx
import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlencode, quote


class ArchiveSnapshot:
    """Represents a single archived page snapshot"""

    def __init__(self, url: str, timestamp: str, source: str, title: str = None):
        self.url = url
        self.timestamp = timestamp  # ISO format: YYYY-MM-DDTHH:MM:SSZ
        self.source = source  # 'wayback', 'commoncrawl', 'archive.today', etc.
        self.title = title or url
        self.date = self._parse_timestamp(timestamp)

    def _parse_timestamp(self, ts: str) -> str:
        """Parse timestamp to readable date"""
        try:
            if len(ts) == 14:  # YYYYMMDDHHmmss
                dt = datetime.strptime(ts, '%Y%m%d%H%M%S')
            else:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return dt.strftime('%B %d, %Y')
        except:
            return ts

    def __repr__(self):
        return f"<Snapshot {self.source} {self.date}>"


class WaybackMachineEngine:
    """Query Internet Archive Wayback Machine"""

    BASE_URL = "https://web.archive.org"
    CDX_API = f"{BASE_URL}/cdx/search/cdx"

    @staticmethod
    def search(url: str, count: int = 100) -> List[ArchiveSnapshot]:
        """Get snapshots from Wayback Machine"""

        params = {
            'url': url,
            'output': 'json',
            'filter': 'statuscode:200',
            'collapse': 'urlkey',
            'limit': count
        }

        try:
            resp = httpx.get(WaybackMachineEngine.CDX_API, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            if not data or len(data) < 2:
                return []

            snapshots = []
            for row in data[1:]:
                timestamp, statuscode, original = row[0], row[1], row[2]
                snapshot = ArchiveSnapshot(
                    url=original,
                    timestamp=timestamp,
                    source='wayback',
                    title=f"Wayback Machine - {original}"
                )
                snapshots.append(snapshot)

            return snapshots
        except Exception as e:
            print(f"Wayback error: {e}")
            return []

    @staticmethod
    def get_snapshot_url(url: str, timestamp: str) -> str:
        """Get direct link to archived snapshot"""
        # Convert timestamp to wayback format if needed
        ts = timestamp.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')
        if len(ts) > 14:
            ts = ts[:14]
        return f"{WaybackMachineEngine.BASE_URL}/web/{ts}/{url}"


class CommonCrawlEngine:
    """Query Common Crawl index"""

    CDX_API = "https://index.commoncrawl.org"

    @staticmethod
    def search(url: str, count: int = 100) -> List[ArchiveSnapshot]:
        """Get snapshots from Common Crawl"""

        params = {
            'url': url,
            'output': 'json',
            'limit': count
        }

        try:
            resp = httpx.get(f"{CommonCrawlEngine.CDX_API}/CC-MAIN-2024-10-index", 
                           params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return []

            snapshots = []
            for item in data:
                snapshot = ArchiveSnapshot(
                    url=item.get('url'),
                    timestamp=item.get('timestamp'),
                    source='common_crawl',
                    title=f"Common Crawl - {item.get('url')}"
                )
                snapshots.append(snapshot)

            return snapshots
        except Exception as e:
            print(f"Common Crawl error: {e}")
            return []


class MementoAggregatorEngine:
    """Query Memento Time Travel (aggregates multiple archives)"""

    BASE_URL = "https://timetravel.mementoweb.org"

    @staticmethod
    def search(url: str, count: int = 100) -> List[ArchiveSnapshot]:
        """Get snapshots from all available archives via Memento"""

        params = {
            'url': url,
            'output': 'json'
        }

        try:
            resp = httpx.get(f"{MementoAggregatorEngine.BASE_URL}/list/json/{url}",
                           timeout=5)
            resp.raise_for_status()
            data = resp.json()

            snapshots = []
            if 'memento_list' in data and 'memento' in data['memento_list']:
                for memento in data['memento_list']['memento'][:count]:
                    snapshot = ArchiveSnapshot(
                        url=memento.get('uri'),
                        timestamp=memento.get('datetime'),
                        source='memento',
                        title=f"Archived - {memento.get('datetime', '')}"
                    )
                    snapshots.append(snapshot)

            return snapshots
        except Exception as e:
            print(f"Memento error: {e}")
            return []


class ArchiveSearchEngine:
    """Unified historical web search engine"""

    def __init__(self):
        self.engines = [
            WaybackMachineEngine(),
            CommonCrawlEngine(),
            MementoAggregatorEngine()
        ]

    def search(self, query: str, count: int = 50) -> Dict:
        """Search all archive sources"""

        results = {
            'query': query,
            'results': [],
            'sources': []
        }

        # Query each engine
        wayback_results = WaybackMachineEngine.search(query, count=count//3)
        common_crawl_results = CommonCrawlEngine.search(query, count=count//3)
        memento_results = MementoAggregatorEngine.search(query, count=count//3)

        # Merge and deduplicate by timestamp
        all_snapshots = wayback_results + common_crawl_results + memento_results
        seen = set()
        unique_snapshots = []

        for snapshot in sorted(all_snapshots, key=lambda x: x.timestamp, reverse=True):
            key = (snapshot.url, snapshot.timestamp)
            if key not in seen:
                seen.add(key)
                unique_snapshots.append(snapshot)

        results['results'] = unique_snapshots[:count]
        results['sources'] = list(set(s.source for s in unique_snapshots))

        return results
```

### SearXNG Engine Configuration

```yaml
# searx/engines/internet_archive.py

name: Internet Archive
engine: searxng.engines.internet_archive.ArchiveSearchEngine
shortcut: ia
timeout: 5

# Options
archive_engines:
  - wayback_machine
  - common_crawl
  - memento

# Cache snapshots for 7 days
cache_time: 604800

# Display format
display_format: compact

# Risk level (low - public archive, no rate limiting)
risk: low
```

---

## Integration with SearXNG

### Option 1: New Engine Tab

Add "Archives" tab to SearXNG settings:

```yaml
searx:
  engines:
    # Existing engines...
    
    # Archives
    - name: wayback_machine
      engine: internet_archive
      
    - name: common_crawl
      engine: internet_archive
      
    - name: memento
      engine: internet_archive
```

### Option 2: Unified Archive Search

Single engine querying all sources:

```python
# searx/engines/archives.py

def request(params, category='web'):
    """Execute archive search"""
    
    query = params['q']
    archive = ArchiveSearchEngine()
    results = archive.search(query, count=100)
    
    return results


def response(resp):
    """Parse archive search results"""
    
    results = []
    data = resp.json()
    
    for snapshot in data['results']:
        results.append({
            'title': f"{snapshot.title} ({snapshot.date})",
            'url': snapshot.url,
            'content': f"Archived by {snapshot.source.upper()}",
            'type': 'archive',
            'engines': [snapshot.source],
            'template': 'default'
        })
    
    return results
```

### Option 3: Add to Existing Search

Show archive availability for any search:

```python
# Enhance results with archive links
for result in results:
    # Check if URL has Wayback snapshots
    wayback_url = f"https://web.archive.org/web/*/{result['url']}"
    result['archive_link'] = wayback_url
    
    # Add archive icon/badge
    result['archive_available'] = True
```

---

## API Comparison

| Archive | API | Rate Limit | Response Time | Coverage |
|---------|-----|-----------|---------------|----------|
| **Wayback Machine** | CDX REST | Generous | 1-3s | 700B pages |
| **Common Crawl** | CDX REST | Generous | 2-5s | 80B pages |
| **Memento** | Memento Protocol | Generous | 2-4s | Multi-archive |
| **Archive.today** | Web UI only | Strict | 3-5s | 100M pages |
| **Perma.cc** | REST API | Moderate | 1-2s | 200M links |
| **UK Web Archive** | OAI-PMH | Moderate | 2-4s | UK content |

---

## Performance Optimization

### Caching Strategy

```python
class ArchiveCache:
    """Cache archive queries to reduce API calls"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 7 * 24 * 3600  # 7 days
    
    def get_snapshots(self, url):
        """Get cached snapshots or query live"""
        
        cache_key = f"archive:{url}"
        cached = self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Query all archives
        results = ArchiveSearchEngine().search(url)
        
        # Cache for 7 days
        self.redis.setex(cache_key, self.ttl, json.dumps(results))
        
        return results
```

### Parallel Queries

```python
import asyncio

async def search_all_archives(url):
    """Query all archives in parallel"""
    
    tasks = [
        asyncio.to_thread(WaybackMachineEngine.search, url),
        asyncio.to_thread(CommonCrawlEngine.search, url),
        asyncio.to_thread(MementoAggregatorEngine.search, url)
    ]
    
    results = await asyncio.gather(*tasks)
    return [r for results in results for r in results]
```

---

## Deployment Checklist

### Phase 1: Core (Week 1)
- [ ] Implement WaybackMachineEngine
- [ ] Test CDX API queries
- [ ] Add caching layer
- [ ] Create SearXNG engine wrapper

### Phase 2: Expansion (Week 2)
- [ ] Add CommonCrawlEngine
- [ ] Add MementoAggregatorEngine
- [ ] Implement deduplication
- [ ] Test error handling

### Phase 3: Integration (Week 3)
- [ ] Add to SearXNG settings.yml
- [ ] Create UI templates
- [ ] Test end-to-end search
- [ ] Performance monitoring

### Phase 4: Polish (Week 4)
- [ ] Add regional archives (Arquivo.pt, UK Web Archive)
- [ ] Implement Archive.today/Perma.cc support
- [ ] Add replay capability (OldWeb.today links)
- [ ] Documentation

---

## Usage Examples

### Search for Historical Version

```bash
# Query SearXNG for archive versions of example.com
curl "https://searxng.example.com/search?q=example.com%20archive&engine=wayback_machine"

# Returns: Snapshots from 1996-present
```

### Direct Archive Links

```
Wayback Machine:     https://web.archive.org/web/20240101/example.com
Common Crawl:        https://index.commoncrawl.org/
Memento:             https://timetravel.mementoweb.org/list/json/example.com
Archive.today:       https://archive.today/?url=example.com
Perma.cc:            https://perma.cc/api/v1/captures?url=example.com
```

---

## Benefits

✅ **Comprehensive Coverage** - 780+ billion archived pages
✅ **Multiple Sources** - Reduce dependency on single archive
✅ **Regional Support** - Portuguese, UK, LoC archives
✅ **Free** - All APIs are free or have generous free tiers
✅ **Proven** - Wayback Machine trusted for 25+ years
✅ **Legal Discovery** - Archive.today, Perma.cc for citations
✅ **Federated** - Memento protocol enables multi-source queries

---

## Next Steps

1. Implement core engines (Wayback + Common Crawl + Memento)
2. Deploy to SearXNG staging
3. Test with representative queries
4. Monitor API rates and performance
5. Add regional archives as needed
6. Consider replay capability (OldWeb.today integration)

---

## References

- Wayback Machine API: https://archive.org/help/wayback_api.php
- Common Crawl CDX: https://commoncrawl.org/the-commons/crawling-the-commons/
- Memento RFC: https://tools.ietf.org/html/rfc7089
- Archive.org API: https://archive.org/services/docs/api/index.html

**Status:** Ready for implementation 🚀
