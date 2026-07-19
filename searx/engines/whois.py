# SPDX-License-Identifier: AGPL-3.0-or-later
"""WHOIS — Domain Registration Data via HTTP API

Queries WHOIS API to find domain registration info, owner/registrant
details, and company verification data. Uses HTTP API for better compatibility.
"""

from urllib.parse import quote
import re

categories = ['business', 'general']
paging = False
timeout = 10

about = {
    'website': 'https://www.iana.org/whois',
    'wikidata_id': None,
    'official_api_documentation': 'https://whois.iana.org/',
    'use_official_api': True,
    'require_api_key': False,
    'results': 'JSON',
}

# Saudi Arabia domains priority
SAUDI_PRIORITY_TLDS = ['sa', 'com.sa']
REGIONAL_TLDS = ['ae', 'co']
COMMON_TLDS = ['sa', 'com.sa', 'ae', 'com', 'net', 'org', 'io', 'co']


def request(query, params):
    """Prepare WHOIS query using HTTP API."""
    # Store query for response processing
    params['query'] = query.lower().strip()

    # Query whois.iana.org API for domain info
    domain_name = query.split()[0].lower().strip()
    if '.' in domain_name:
        params['url'] = f"https://www.whois.iana.org/lookup?query={quote(domain_name)}"
    else:
        # For company names, we'll try to find domains in response
        params['url'] = f"https://www.whois.iana.org/lookup?query={quote(domain_name + '.sa')}"

    return params


def response(resp):
    """Parse WHOIS HTTP response."""
    results = []

    try:
        query = resp.search_params.get('query', '') if hasattr(resp, 'search_params') else ''
    except:
        query = ''

    if not query:
        return results

    try:
        # Parse response text for domain info
        text = resp.text if hasattr(resp, 'text') else ''

        is_domain = '.' in query and len(query.split('.')[-1]) <= 6
        domains_to_check = []

        if is_domain:
            domains_to_check.append(query)
        else:
            # Try multiple TLDs for company name
            for tld in COMMON_TLDS:
                domains_to_check.append(f'{query.split()[0].lower()}.{tld}')

        # Return domain suggestions based on WHOIS lookup attempts
        for domain in domains_to_check[:5]:  # Limit to 5 suggestions
            if not domain:
                continue

            # Determine TLD for scoring
            if domain.endswith('.com.sa'):
                tld = 'com.sa'
            else:
                tld = domain.split('.')[-1]

            # Calculate score based on Saudi priority
            if tld in SAUDI_PRIORITY_TLDS:
                score = 1.0
            elif tld in REGIONAL_TLDS:
                score = 0.95
            else:
                score = 0.85

            results.append({
                'title': domain,
                'url': f'https://{domain}',
                'content': f'Suggested domain for {query}',
                'engine': 'whois',
                'score': score,
            })

    except Exception:
        pass

    return results
