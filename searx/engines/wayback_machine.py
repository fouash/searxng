"""
Internet Archive Wayback Machine engine

Provides access to 700+ billion archived web pages from 1996-present.
Uses CDX API for historical snapshot queries.

Features:
- Full-text archive search
- Multiple snapshots per URL
- HTTP status code filtering
- Timestamp-based sorting
"""

import httpx
from urllib.parse import urlencode, urlparse
from datetime import datetime

about = {
    'website': 'https://web.archive.org/',
    'wikidata_id': 'Q590141',
    'official_api_documentation': 'https://archive.org/help/wayback_api.php',
    'use_official_api': True,
    'results': 'JSON'
}

paging = True
page_size = 50
categories = ['web', 'image', 'social media']
engine_type = 'online'
language = 'en'

API_ENDPOINT = 'https://web.archive.org/cdx/search/cdx'
ARCHIVE_BASE = 'https://web.archive.org'


def request(params):
    """Build request to Wayback Machine CDX API"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    # Parse URL or search query
    if query.startswith('http://') or query.startswith('https://'):
        search_url = query
    else:
        # Assume it's a domain or URL pattern
        search_url = query if query.startswith('*') else f"*{query}*"

    # Calculate pagination
    offset = (page - 1) * page_size

    payload = {
        'url': search_url,
        'output': 'json',
        'filter': 'statuscode:200',  # Only successful captures
        'collapse': 'urlkey',  # Deduplicate URLs
        'sort': 'reverse',  # Newest first
        'limit': page_size,
        'offset': offset
    }

    return {
        'url': API_ENDPOINT,
        'params': payload,
        'timeout': 5
    }


def response(resp):
    """Parse Wayback Machine CDX API response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    # First row is column headers, skip it
    if not data or len(data) < 2:
        return results

    headers = data[0]
    rows = data[1:]

    # Find column indices
    try:
        url_idx = headers.index('original')
        timestamp_idx = headers.index('timestamp')
        status_idx = headers.index('statuscode')
    except ValueError:
        return results

    # Parse each snapshot
    for row in rows:
        if len(row) <= max(url_idx, timestamp_idx, status_idx):
            continue

        url = row[url_idx]
        timestamp = row[timestamp_idx]
        status = row[status_idx]

        # Parse timestamp
        try:
            dt = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            date_str = dt.strftime('%B %d, %Y at %H:%M:%S UTC')
        except:
            date_str = timestamp

        # Build archive URL
        archive_url = f"{ARCHIVE_BASE}/web/{timestamp}/{url}"

        results.append({
            'title': f"[{date_str}] {url}",
            'url': archive_url,
            'content': f"HTTP {status} • {date_str}",
            'engine': 'Wayback Machine',
            'engines': ['wayback_machine'],
            'parsed_url': url,
            'timestamp': timestamp,
            'date': date_str
        })

    return results
