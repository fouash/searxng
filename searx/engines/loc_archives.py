"""
Library of Congress Web Archives engine

Selective archival of US government and cultural content.
Includes congressional websites, library collections, and government records.

Features:
- US government content
- Library collections
- Cultural heritage
- Supreme Court records
"""

import httpx
from datetime import datetime

about = {
    'website': 'https://www.loc.gov/web-archives/',
    'wikidata_id': 'Q131454',
    'official_api_documentation': 'https://www.loc.gov/web-archives/about/',
    'use_official_api': True,
    'results': 'JSON'
}

categories = ['web', 'science']
engine_type = 'online'
paging = True
page_size = 50
language = 'en'

API_BASE = 'https://www.loc.gov'


def request(params):
    """Build request to Library of Congress Web Archives"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    if not query:
        return {}

    offset = (page - 1) * page_size

    return {
        'url': f"{API_BASE}/collections/web-archives/search",
        'params': {
            'q': query,
            'start': offset,
            'rows': page_size
        },
        'timeout': 5
    }


def response(resp):
    """Parse Library of Congress search response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    # LoC returns search results in various formats
    items = data.get('results', [])

    for item in items:
        try:
            url = item.get('url', '')
            title = item.get('title', url)
            date = item.get('date', '')
            link = item.get('link', '')

            # Parse date
            try:
                if len(str(date)) == 4:  # Year only
                    date_str = str(date)
                elif len(str(date)) == 8:  # YYYYMMDD
                    dt = datetime.strptime(str(date), '%Y%m%d')
                    date_str = dt.strftime('%B %d, %Y')
                else:
                    date_str = str(date)
            except:
                date_str = str(date)

            archive_url = link or url

            results.append({
                'title': f"[{date_str}] {title}",
                'url': archive_url,
                'content': f"Library of Congress Archives • {date_str}",
                'engine': 'Library of Congress',
                'engines': ['loc_archives'],
                'timestamp': str(date),
                'date': date_str,
                'metadata': {
                    'collection': item.get('collection', ''),
                    'source': 'Library of Congress'
                }
            })
        except Exception:
            continue

    return results
