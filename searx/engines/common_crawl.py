"""
Common Crawl engine

Access 80+ billion indexed web pages from monthly crawls.
Provides bulk historical data and WARC file references.

Features:
- Large-scale historical index
- WARC file metadata
- Monthly crawl data
- Content-type detection
"""

import httpx
from datetime import datetime

about = {
    'website': 'https://commoncrawl.org/',
    'wikidata_id': 'Q21006196',
    'official_api_documentation': 'https://commoncrawl.org/the-commons/crawling-the-commons/',
    'use_official_api': True,
    'results': 'JSON'
}

paging = True
page_size = 50
categories = ['web', 'science', 'data']
engine_type = 'online'
language = 'en'

# Common Crawl maintains multiple monthly indexes
# Use the latest 2024-10 index by default
API_ENDPOINTS = [
    'https://index.commoncrawl.org/CC-MAIN-2024-10-index',
    'https://index.commoncrawl.org/CC-MAIN-2024-09-index',
    'https://index.commoncrawl.org/CC-MAIN-2024-08-index',
]


def request(params):
    """Build request to Common Crawl CDX API"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    # Parse URL
    if not query.startswith('http://') and not query.startswith('https://'):
        if '.' in query:
            query = f"http://{query}"
        else:
            query = f"http://{query}.com"

    offset = (page - 1) * page_size

    payload = {
        'url': query,
        'output': 'json',
        'limit': page_size,
        'offset': offset
    }

    return {
        'url': API_ENDPOINTS[0],  # Use latest index
        'params': payload,
        'timeout': 5
    }


def response(resp):
    """Parse Common Crawl CDX API response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    if not data:
        return results

    # Common Crawl returns array of capture objects
    captures = data if isinstance(data, list) else data.get('captures', [])

    for item in captures:
        try:
            url = item.get('url', '')
            timestamp = item.get('timestamp', '')
            status = item.get('status_code', '200')

            # Parse timestamp
            try:
                dt = datetime.strptime(str(timestamp)[:14], '%Y%m%d%H%M%S')
                date_str = dt.strftime('%B %d, %Y')
            except:
                date_str = timestamp

            # Format result
            results.append({
                'title': f"[{date_str}] {url}",
                'url': url,
                'content': f"HTTP {status} • Common Crawl Index",
                'engine': 'Common Crawl',
                'engines': ['common_crawl'],
                'parsed_url': url,
                'timestamp': timestamp,
                'date': date_str,
                'metadata': {
                    'warc_filename': item.get('filename'),
                    'warc_offset': item.get('offset'),
                    'warc_length': item.get('length')
                }
            })
        except Exception:
            continue

    return results
