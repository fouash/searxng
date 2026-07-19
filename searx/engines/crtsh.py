# SPDX-License-Identifier: AGPL-3.0-or-later
"""crt.sh — Certificate Transparency Log Search

Finds all registered domains for a company by querying SSL certificate records.
Useful for company domain discovery: enter a company name and get all their domains.
"""

from urllib.parse import quote

categories = ['general', 'business']
paging = False
timeout = 10

# Saudi Arabia domain priority settings
SAUDI_TLDS = {'.sa': 1.0, '.com.sa': 1.0, '.gov.sa': 1.0, '.net.sa': 1.0}
REGIONAL_TLDS = {'.ae': 0.95, '.com.ae': 0.95, '.co': 0.9}

about = {
    'website': 'https://crt.sh',
    'wikidata_id': None,
    'official_api_documentation': 'https://crt.sh',
    'use_official_api': True,
    'require_api_key': False,
    'results': 'JSON',
}


def request(query, params):
    """Query crt.sh for SSL certificates."""
    search_query = f"%.{query}" if '.' not in query else query

    params['url'] = f"https://crt.sh/?q={quote(search_query)}&output=json"
    params['headers'] = {
        'User-Agent': 'SearXNG/crt.sh-engine',
    }

    return params


def response(resp):
    """Parse crt.sh JSON response with Saudi Arabia domain priority."""
    results = []

    try:
        data = resp.json()
    except Exception:
        return results

    if not data:
        return results

    seen_domains = set()

    for cert in data:
        name_value = cert.get('name_value', '')
        if not name_value:
            continue

        domains = [d.strip() for d in name_value.split('\n') if d.strip()]

        for domain in domains:
            if domain.startswith('*.'):
                domain = domain[2:]

            if domain not in seen_domains:
                seen_domains.add(domain)

                # Calculate score based on Saudi Arabia priority
                score = 0.8  # Default score
                for tld, tld_score in SAUDI_TLDS.items():
                    if domain.endswith(tld):
                        score = tld_score
                        break
                else:
                    for tld, tld_score in REGIONAL_TLDS.items():
                        if domain.endswith(tld):
                            score = tld_score
                            break

                results.append({
                    'title': domain,
                    'url': f'https://{domain}',
                    'content': f'SSL certificate found for {domain}',
                    'engine': 'crtsh',
                    'score': score,
                })

    return results
