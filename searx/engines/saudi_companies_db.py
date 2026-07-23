# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saudi Companies Database — Local offline search for Saudi domains

Searches locally downloaded Saudi company domains from Certificate Transparency logs.
No external API calls required - fully offline operation.
Supports both English and Arabic company name searches via company mappings.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)

categories = ['general', 'business']
engine_type = 'offline'
paging = False
timeout = 5
language = 'en'

about = {
    'website': 'https://crt.sh',
    'wikidata_id': None,
    'official_api_documentation': 'https://crt.sh',
    'use_official_api': False,
    'results': 'Local database (Certificate Transparency) + Company Mappings',
}

# Lazy-loaded databases
_domains_cache = None
_mappings_cache = None
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
        Path('/usr/local/searxng/data/domains/saudi_domains.json'),
    ]

    for db_path in possible_paths:
        if db_path.exists():
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _cache_timestamp = data.get('downloaded_at', 'Unknown')
                    num_domains = len(data.get('saudi_domains', []))
                    logger.info(f'Loaded {num_domains} Saudi domains from {db_path}')

                    # Build efficient lookup structures
                    domains_data = {
                        'saudi': set(data.get('saudi_domains', [])),
                        'regional': set(data.get('regional_domains', [])),
                    }

                    return domains_data

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f'Failed to load {db_path}: {e}')
                continue

    logger.warning('No Saudi domains database found')
    return None


def _load_company_mappings() -> Optional[Dict]:
    """Load company name mappings (Arabic/English names and domain keywords)."""
    possible_paths = [
        Path(__file__).parent.parent.parent / 'data' / 'domains' / 'company_mappings.json',
        Path('/etc/searxng/domains/company_mappings.json'),
        Path('data/domains/company_mappings.json'),
        Path('/usr/local/searxng/data/domains/company_mappings.json'),
    ]

    for mapping_path in possible_paths:
        if mapping_path.exists():
            try:
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f'Loaded company mappings from {mapping_path}')
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f'Failed to load {mapping_path}: {e}')
                continue

    logger.debug('No company mappings found (optional)')
    return None


def _get_domains():
    """Get domains database, with lazy loading and caching."""
    global _domains_cache

    if _domains_cache is None:
        _domains_cache = _load_domains_database()

    return _domains_cache


def _get_mappings():
    """Get company mappings, with lazy loading and caching."""
    global _mappings_cache

    if _mappings_cache is None:
        _mappings_cache = _load_company_mappings()

    return _mappings_cache


def _find_mapped_keywords(query: str) -> List[str]:
    """Find domain keywords from company name mappings (Arabic or English)."""
    mappings = _get_mappings()
    if not mappings or 'company_mappings' not in mappings:
        return []

    query_lower = query.lower().strip()
    keywords = []

    for company in mappings['company_mappings']:
        # Check Arabic names
        ar_names = company.get('ar_names', [])
        for ar_name in ar_names:
            if ar_name.lower().strip() == query_lower:
                keywords.append(company['domain_keyword'].lower())
                break

        # Check English names
        en_names = company.get('en_names', [])
        for en_name in en_names:
            if en_name.lower().strip() == query_lower:
                keywords.append(company['domain_keyword'].lower())
                break

    return list(set(keywords))


def request(params):
    """Prepare search request - handled locally (no HTTP call needed)."""
    query = params.get('q', '').lower().strip()
    params['_query'] = query
    return params


def response(resp):
    """Search local domain database using query and company mappings."""
    results = []

    # Extract query from different possible sources
    query = ''
    try:
        if hasattr(resp, 'get'):
            query = resp.get('_query', '').lower().strip()
        elif hasattr(resp, 'search_params'):
            query = resp.search_params.get('_query', '').lower().strip()
        elif hasattr(resp, 'json'):
            data = resp.json()
            query = data.get('_query', '').lower().strip()
    except Exception as e:
        logger.warning(f'Error extracting query from response: {e}')
        return results

    if not query:
        logger.debug('Empty query received')
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
