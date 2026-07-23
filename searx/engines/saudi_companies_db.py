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


def request(params):
    """Build local search request"""
    query = params.get('q', '').lower().strip()
    if not query:
        return {}
    return {'url': 'about:blank', 'params': params}


def response(resp):
    """Perform offline search"""
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
            })

    except Exception:
        pass

    return results

    # Load domains database
    domains_db = _get_domains()
    if not domains_db:
        logger.warning('No domains database loaded')
        return results

    # Combine all domains for searching
    all_domains = domains_db.get('saudi', set()) | domains_db.get('regional', set())
    logger.debug(f'Searching {len(all_domains)} domains for query: {query}')

    # Build list of search keywords from query and mappings
    search_keywords = [query]

    # Add mapped domain keywords if query matches a known company name
    mapped_keywords = _find_mapped_keywords(query)
    if mapped_keywords:
        search_keywords.extend(mapped_keywords)

    matched_domains = []
    seen_domains = set()

    # Search for each keyword
    for search_key in search_keywords:
        for domain in all_domains:
            if domain in seen_domains:
                continue

            score = 0.0

            # Strategy 1: Exact matches or subdomains
            if domain == search_key:
                score = 1.0
            elif domain.startswith(search_key + '.'):
                score = 0.95
            elif domain.startswith(search_key + '-'):
                score = 0.90

            # Strategy 2: Contains search term
            elif search_key in domain:
                score = 0.85

            # Strategy 3: Word boundary matches (domain name before first dot)
            else:
                domain_name = domain.split('.')[0]
                if search_key == domain_name:
                    score = 0.90
                elif search_key in domain_name and len(search_key) > 2:
                    score = 0.80

            if score > 0:
                # Boost Saudi domains
                if domain in domains_db.get('saudi', set()):
                    score = min(1.0, score + 0.10)

                matched_domains.append({
                    'domain': domain,
                    'score': score
                })
                seen_domains.add(domain)

    # Sort by score (highest first)
    matched_domains.sort(key=lambda x: x['score'], reverse=True)

    # Convert to SearXNG result format
    for item in matched_domains:
        domain = item['domain']
        results.append({
            'title': domain,
            'url': f'https://{domain}',
            'content': f'Saudi company domain - Found in Certificate Transparency logs',
            'engine': 'saudi_companies_db',
            'score': item['score'],
        })

    logger.info(f'Found {len(results)} results for query: {query}')
    return results
