# SPDX-License-Identifier: AGPL-3.0-or-later
"""WHOIS — Domain Registration Data Lookup

Queries WHOIS registries to find domain registration info, owner/registrant
details, and company verification data. Useful for verifying company ownership
of domains and finding company details from domain records.
"""

import socket
import re

categories = ['business', 'general']
paging = False
timeout = 15

about = {
    'website': 'https://www.iana.org/whois',
    'wikidata_id': None,
    'official_api_documentation': None,
    'use_official_api': False,
    'require_api_key': False,
    'results': 'Text',
}

WHOIS_SERVERS = {
    'com': 'whois.verisign-grs.com',
    'net': 'whois.verisign-grs.com',
    'org': 'whois.pir.org',
    'info': 'whois.afilias.net',
    'biz': 'whois.neulevel.biz',
    'sa': 'whois.nic.net.sa',
    'ae': 'whois.aeda.net.ae',
    'uk': 'whois.nic.uk',
    'de': 'whois.denic.de',
    'fr': 'whois.afnic.fr',
}

COMMON_TLDS = ['com', 'net', 'org', 'co', 'sa', 'ae', 'io']


def query_whois_server(domain, tld):
    """Query WHOIS server for domain information."""
    whois_server = WHOIS_SERVERS.get(tld, f'whois.{tld}')

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((whois_server, 43))
        sock.sendall(f'{domain}\r\n'.encode())

        response = b''
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data

        sock.close()
        return response.decode('utf-8', errors='ignore')
    except (socket.timeout, socket.error, ConnectionRefusedError, OSError):
        return None


def extract_whois_info(whois_data):
    """Extract registration info from WHOIS response."""
    if not whois_data:
        return {}

    info = {}
    patterns = {
        'registrant': [r'Registrant.*?:\s*(.+)', r'Registrant Name:\s*(.+)'],
        'registrant_org': [r'Registrant Organization:\s*(.+)', r'Registrant Company:\s*(.+)'],
        'registrar': [r'Registrar:\s*(.+)', r'Sponsoring Registrar:\s*(.+)'],
        'created': [r'Creation Date:\s*(.+)', r'Created Date:\s*(.+)'],
        'expires': [r'Expir.*?Date:\s*(.+)', r'Expiry Date:\s*(.+)'],
    }

    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, whois_data, re.IGNORECASE | re.MULTILINE)
            if match:
                info[key] = match.group(1).strip()
                break

    return info


def request(query, params):
    """Prepare WHOIS query."""
    params['whois_query'] = query.lower().strip()
    return params


def response(resp):
    """Parse WHOIS response."""
    results = []
    query = resp.search_params.get('whois_query', '')

    if not query:
        return results

    is_domain = '.' in query and len(query.split('.')[-1]) <= 6
    domains_to_check = []

    if is_domain:
        domains_to_check.append(query)
    else:
        for tld in COMMON_TLDS:
            domains_to_check.append(f'{query.split()[0].lower()}.{tld}')

    seen_domains = set()

    for domain in domains_to_check:
        if domain in seen_domains:
            continue

        parts = domain.split('.')
        if len(parts) < 2:
            continue

        tld = parts[-1]
        seen_domains.add(domain)

        whois_data = query_whois_server(domain, tld)
        if not whois_data or 'No Data Found' in whois_data or 'Not found' in whois_data:
            continue

        info = extract_whois_info(whois_data)

        if info:
            registrant = info.get('registrant_org') or info.get('registrant', 'Unknown')
            created = info.get('created', '')
            expires = info.get('expires', '')

            content = f'Registrant: {registrant}'
            if created:
                content += f' | Created: {created}'
            if expires:
                content += f' | Expires: {expires}'

            results.append({
                'title': domain,
                'url': f'https://{domain}',
                'content': content,
                'engine': 'whois',
                'score': 0.9,
            })

    return results
