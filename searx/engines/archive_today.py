"""
Archive.today / Archive.is engine

Permanent preservation of web pages with screenshot capability.
Commonly used for citation and proof preservation.

Features:
- Permanent link generation
- Screenshot capture
- Redaction capability
- No deletion (permanent preservation)
"""

import httpx
from datetime import datetime
from urllib.parse import quote

about = {
    'website': 'https://archive.today/',
    'wikidata_id': None,
    'official_api_documentation': 'https://archive.today/services/find',
    'use_official_api': True,
    'results': 'JSON',
    'language': 'en'
}

categories = ['web', 'social media']
engine_type = 'online'
paging = False

API_BASE = 'https://archive.today'


def request(params):
    """Build request to Archive.today search"""

    query = params.get('q', '')

    if not query:
        return {}

    # Archive.today search API
    return {
        'url': f"{API_BASE}/services/find",
        'params': {
            'url': query,
            'year': '*',
            'output': 'json'
        },
        'timeout': 5
    }


def response(resp):
    """Parse Archive.today search results"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    if not data or 'results' not in data:
        return results

    for snapshot in data.get('results', []):
        try:
            url = snapshot.get('url', '')
            timestamp = snapshot.get('timestamp', '')

            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%B %d, %Y')
            except:
                date_str = timestamp

            archive_url = f"{API_BASE}/{timestamp}/{url}"

            results.append({
                'title': f"[{date_str}] {url}",
                'url': archive_url,
                'content': f"Permanent archive • {date_str}",
                'engine': 'Archive.today',
                'engines': ['archive_today'],
                'timestamp': timestamp,
                'date': date_str
            })
        except Exception:
            continue

    return results
