"""
Memento Time Travel engine

Federated search across multiple web archives using Memento Protocol (RFC 7089).
Aggregates results from Wayback Machine, Archive.today, UK Web Archive, etc.

Features:
- Multi-archive search
- Memento Protocol RFC 7089 compliance
- Unified timestamp sorting
- Archive source identification
"""

import httpx
from datetime import datetime
from urllib.parse import quote

about = {
    'website': 'https://timetravel.mementoweb.org/',
    'wikidata_id': None,
    'official_api_documentation': 'https://mementoweb.org/guide/quick-start/',
    'use_official_api': True,
    'results': 'JSON'
}

paging = True
page_size = 50
categories = ['web', 'social media', 'search']
engine_type = 'online'
language = 'en'

API_BASE = 'https://timetravel.mementoweb.org'


def request(params):
    """Build request to Memento Time Travel API"""

    query = params.get('q', '')
    page = params.get('pageno', 1)

    # Ensure URL format
    if not query.startswith('http://') and not query.startswith('https://'):
        if '.' in query:
            query = f"http://{query}"
        else:
            return {}

    return {
        'url': f"{API_BASE}/list/json/{query}",
        'timeout': 5
    }


def response(resp):
    """Parse Memento Time Travel API response"""

    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    if not data or 'memento_list' not in data:
        return results

    memento_list = data['memento_list']
    if 'memento' not in memento_list:
        return results

    mementos = memento_list['memento']
    if not isinstance(mementos, list):
        mementos = [mementos]

    # Parse each memento (archived version)
    for memento in mementos:
        try:
            uri = memento.get('uri', '')
            datetime_str = memento.get('datetime', '')

            # Extract archive source from URI
            if 'web.archive.org' in uri:
                source = 'Wayback Machine'
                shortname = 'wa'
            elif 'archive.today' in uri or 'archive.is' in uri:
                source = 'Archive.today'
                shortname = 'ar'
            elif 'webarchive.org.uk' in uri:
                source = 'UK Web Archive'
                shortname = 'uk'
            elif 'arquivo.pt' in uri:
                source = 'Arquivo.pt'
                shortname = 'pt'
            else:
                source = 'Memento Archive'
                shortname = 'mem'

            # Parse datetime
            try:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                date_str = dt.strftime('%B %d, %Y')
            except:
                date_str = datetime_str

            results.append({
                'title': f"[{date_str}] {source}",
                'url': uri,
                'content': f"Archived by {source}",
                'engine': source,
                'engines': [f'memento_{shortname}'],
                'timestamp': datetime_str,
                'date': date_str,
                'archive_source': source
            })
        except Exception:
            continue

    return results
