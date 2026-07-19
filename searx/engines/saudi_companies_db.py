# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saudi Companies Database — Local offline search for Saudi domains

Searches locally downloaded Saudi company domains from Certificate Transparency logs.
No external API calls required - fully offline operation.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Set

categories = ['general', 'business']
paging = False
timeout = 5

about = {
    'website': 'https://crt.sh',
    'wikidata_id': None,
    'official_api_documentation': 'https://crt.sh',
    'use_official_api': False,
    'require_api_key': False,
    'results': 'Local database (Certificate Transparency)',
}

# Lazy-loaded domains database
_domains_cache = None
_cache_timestamp = None


def _load_domains_database():
    """Load Saudi domains from JSON database file."""
    global _domains_cache, _cache_timestamp

    # Try multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent.parent / 'data' / 'domains' / 'saudi_domains.json',
        Path('/etc/searxng/domains/saudi_domains.json'),
        Path('/var/lib/searxng/domains/saudi_domains.json'),
        Path('data/domains/saudi_domains.json'),
    ]

    for db_path in possible_paths:
        if db_path.exists():
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _cache_timestamp = data.get('downloaded_at', 'Unknown')

                    # Build efficient lookup structures
                    domains_data = {
                        'saudi': set(data.get('saudi_domains', [])),
                        'regional': set(data.get('regional_domains', [])),
                    }

                    return domains_data

            except (json.JSONDecodeError, IOError) as e:
                continue

    return None


def _get_domains():
    """Get domains database, with lazy loading and caching."""
    global _domains_cache

    if _domains_cache is None:
        _domains_cache = _load_domains_database()

    return _domains_cache


def request(query, params):
    """Prepare search request - handled locally."""
    # Store query for response function
    params['query'] = query.lower().strip()
    params['local_search'] = True

    return params


def response(resp):
    """Search local domain database."""
    results = []

    try:
        query = resp.search_params.get('query', '').lower().strip()
    except Exception:
        return results

    if not query:
        return results

    # Load domains database
    domains_db = _get_domains()

    if not domains_db:
        return results

    # Combine all domains for searching
    all_domains = domains_db.get('saudi', set()) | domains_db.get('regional', set())

    # Search strategies:
    # 1. Exact domain match or subdomain
    # 2. Domain name contains search term
    # 3. Company name pattern matching

    matched_domains = []

    for domain in all_domains:
        score = 0.0

        # Strategy 1: Exact matches or subdomains
        if domain == query:
            score = 1.0
        elif domain.startswith(query + '.'):
            score = 0.95
        elif domain.startswith(query + '-'):
            score = 0.90

        # Strategy 2: Contains search term
        elif query in domain:
            score = 0.85

        # Strategy 3: Word boundary matches
        else:
            # Check if query matches domain name (before first dot)
            domain_name = domain.split('.')[0]
            if query == domain_name:
                score = 0.90
            elif query in domain_name and len(query) > 2:
                score = 0.80

        if score > 0:
            # Boost Saudi domains
            if domain in domains_db.get('saudi', set()):
                score = min(1.0, score + 0.10)

            matched_domains.append({
                'domain': domain,
                'score': score
            })

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

    return results
