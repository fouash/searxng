"""
Perma.cc engine

Academic and legal citation preservation.
200+ million permanent links for scholarly citations.

Features:
- Permanent link generation
- DOI/URL preservation
- Academic/legal use
- No paywalls
"""

import httpx
from datetime import datetime

about = {
    'website': 'https://perma.cc/',
    'wikidata_id': None,
    'official_api_documentation': 'https://perma.cc/api/v1/',
    'use_official_api': True,
    'requires_api_key': False,
    'results': 'JSON',
    'language': 'en',
    'timeout': 5.0
}

categories = ['web', 'science']
engine_type = 'online'
paging = True
page_size = 50

API_BASE = 'https://perma.cc/api/v1'


def request(params):
    """Build request to Perma.cc API"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    if not query:
        return {}

    offset = (page - 1) * page_size

    return {
        'url': f"{API_BASE}/captures",
        'params': {
            'url': query,
            'limit': page_size,
            'offset': offset,
            'output': 'json'
        },
        'timeout': 5
    }


def response(resp):
    """Parse Perma.cc API response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    captures = data.get('results', [])

    for capture in captures:
        try:
            perma_url = capture.get('url', '')
            capture_url = capture.get('captured_url', '')
            timestamp = capture.get('creation_timestamp', '')

            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%B %d, %Y')
            except:
                date_str = timestamp

            results.append({
                'title': f"[{date_str}] {capture_url}",
                'url': perma_url,
                'content': f"Permanent academic citation • {date_str}",
                'engine': 'Perma.cc',
                'engines': ['perma_cc'],
                'timestamp': timestamp,
                'date': date_str,
                'metadata': {
                    'guid': capture.get('guid'),
                    'title': capture.get('title', '')
                }
            })
        except Exception:
            continue

    return results
