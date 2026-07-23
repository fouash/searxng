"""
Arquivo.pt engine

Portuguese Web Archive - preserves Portuguese web content.
5+ billion pages of Portuguese web from 1996-present.

Features:
- Portuguese web content
- CDX API compatible
- Full-text search
"""

import httpx
from datetime import datetime

about = {
    'website': 'https://arquivo.pt/',
    'wikidata_id': None,
    'official_api_documentation': 'https://arquivo.pt/services',
    'use_official_api': True,
    'results': 'JSON'
}

categories = ['web']
engine_type = 'online'
paging = True
page_size = 50
language = 'pt'

API_BASE = 'https://arquivo.pt'


def request(params):
    """Build request to Arquivo.pt CDX API"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    if not query:
        return {}

    offset = (page - 1) * page_size

    return {
        'url': f"{API_BASE}/noFrame/wayback/*/",
        'params': {
            'url': query,
            'output': 'json',
            'filter': 'statuscode:200',
            'limit': page_size,
            'offset': offset
        },
        'timeout': 5
    }


def response(resp):
    """Parse Arquivo.pt CDX API response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    if not data or len(data) < 2:
        return results

    headers = data[0]
    rows = data[1:]

    # Find column indices
    try:
        url_idx = headers.index('original')
        timestamp_idx = headers.index('timestamp')
    except ValueError:
        return results

    for row in rows:
        if len(row) <= max(url_idx, timestamp_idx):
            continue

        try:
            url = row[url_idx]
            timestamp = row[timestamp_idx]

            # Parse timestamp
            try:
                dt = datetime.strptime(str(timestamp)[:14], '%Y%m%d%H%M%S')
                date_str = dt.strftime('%B %d, %Y')
            except:
                date_str = timestamp

            archive_url = f"{API_BASE}/web/{timestamp}/{url}"

            results.append({
                'title': f"[{date_str}] {url}",
                'url': archive_url,
                'content': f"Portuguese Web Archive • {date_str}",
                'engine': 'Arquivo.pt',
                'engines': ['arquivo_pt'],
                'timestamp': timestamp,
                'date': date_str
            })
        except Exception:
            continue

    return results
