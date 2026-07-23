"""
UK Web Archive engine

Preserves UK web content (.uk domains and UK government).
Includes parliament records, museum collections, and UK cultural content.

Features:
- UK domain focus
- Government records
- Cultural content
"""

import httpx
from datetime import datetime
from urllib.parse import urlencode

about = {
    'website': 'https://www.webarchive.org.uk/',
    'wikidata_id': 'Q28051707',
    'official_api_documentation': 'https://www.webarchive.org.uk/about/api',
    'use_official_api': True,
    'requires_api_key': False,
    'results': 'JSON',
    'language': 'en',
    'timeout': 5.0
}

categories = ['web']
engine_type = 'online'
paging = True
page_size = 50

API_BASE = 'https://www.webarchive.org.uk'


def request(params):
    """Build request to UK Web Archive API"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    if not query:
        return {}

    offset = (page - 1) * page_size

    return {
        'url': f"{API_BASE}/wacsearch/search",
        'params': {
            'query': query,
            'type': 'resource',
            'rows': page_size,
            'offset': offset
        },
        'timeout': 5
    }


def response(resp):
    """Parse UK Web Archive API response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    items = data.get('result', {}).get('results', [])

    for item in items:
        try:
            url = item.get('url', '')
            title = item.get('title', url)
            capture_date = item.get('capture_date', '')
            wayback_id = item.get('wayback_id', '')

            # Parse capture date
            try:
                if len(str(capture_date)) == 14:
                    dt = datetime.strptime(str(capture_date), '%Y%m%d%H%M%S')
                    date_str = dt.strftime('%B %d, %Y')
                else:
                    date_str = str(capture_date)
            except:
                date_str = str(capture_date)

            archive_url = f"{API_BASE}/web/{capture_date}/{url}"

            results.append({
                'title': f"[{date_str}] {title}",
                'url': archive_url,
                'content': f"UK Web Archive • {date_str}",
                'engine': 'UK Web Archive',
                'engines': ['uk_web_archive'],
                'timestamp': str(capture_date),
                'date': date_str,
                'metadata': {
                    'original_url': url
                }
            })
        except Exception:
            continue

    return results
