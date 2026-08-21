"""Saudi Companies Database — Offline search for Saudi domains"""

import json
from pathlib import Path

categories = ['general', 'business']
paging = False
timeout = 5
language = 'en'

about = {
    'website': 'https://crt.sh',
    'wikidata_id': None,
    'official_api_documentation': 'https://crt.sh',
    'use_official_api': False,
    'results': 'Local database (Certificate Transparency)',
}

_domains_cache = None
_mappings_cache = None


def _get_domains():
    global _domains_cache
    if _domains_cache is not None:
        return _domains_cache

    paths = [
        Path(__file__).parent.parent.parent / 'data' / 'domains' / 'saudi_domains.json',
        Path('/usr/local/searxng/data/domains/saudi_domains.json'),
        Path('data/domains/saudi_domains.json'),
    ]

    for path in paths:
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                    _domains_cache = {
                        'saudi': set(data.get('saudi_domains', [])),
                        'regional': set(data.get('regional_domains', [])),
                    }
                    return _domains_cache
            except Exception:
                pass

    return None


def request(query, params):
    """Build local search request using the current SearXNG engine API."""
    search_query = (query or params.get('q', '')).lower().strip()
    if not search_query:
        return {}
    return {'url': 'about:blank', 'params': params}


def response(resp):
    """Perform offline search against the local Saudi domains database."""
    results = []

    try:
        query = resp.params.get('q', '').lower().strip()
        if not query:
            return results

        domains_db = _get_domains()
        if not domains_db:
            return results

        all_domains = domains_db.get('saudi', set()) | domains_db.get('regional', set())
        matched = []

        for domain in all_domains:
            score = 0.0
            if domain == query:
                score = 1.0
            elif domain.startswith(query + '.'):
                score = 0.95
            elif domain.startswith(query + '-'):
                score = 0.90
            elif query in domain:
                score = 0.85

            if score > 0:
                if domain in domains_db.get('saudi', set()):
                    score = min(1.0, score + 0.1)
                matched.append((domain, score))

        matched.sort(key=lambda x: x[1], reverse=True)

        for domain, score in matched:
            results.append({
                'title': domain,
                'url': f'https://{domain}',
                'content': 'Saudi domain (Certificate Transparency logs)',
                'engine': 'saudi_companies_db',
                'score': score,
            })

    except Exception:
        pass

    return results
