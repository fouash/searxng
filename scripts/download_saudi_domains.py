#!/usr/bin/env python3
"""
Download Saudi company domains from crt.sh Certificate Transparency logs.
This creates a local offline database of verified Saudi domains with SSL certificates.
"""

import requests
import json
import time
from typing import Set, List, Dict
from pathlib import Path
from urllib.parse import quote
import sys

# Saudi Arabia domain extensions
SAUDI_DOMAINS = [
    '.sa',
    '.com.sa',
    '.gov.sa',
    '.org.sa',
    '.net.sa',
    '.edu.sa',
    '.ac.sa',
]

REGIONAL_DOMAINS = [
    '.ae',
    '.com.ae',
    '.ae',
    '.co',
]

# crt.sh API endpoint
CRT_SH_API = 'https://crt.sh/'

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'domains'


class CertTransparencyDownloader:
    """Download domains from Certificate Transparency logs."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.timeout = 30
        self.domains: Set[str] = set()
        self.errors: List[str] = []

    def query_domain_extension(self, extension: str) -> Set[str]:
        """Query crt.sh for all domains with a specific extension."""
        domains = set()
        search_query = f'%.{extension}' if extension.startswith('.') else f'%.{extension}'

        try:
            print(f'  Querying {extension}...', end='', flush=True)
            params = {
                'q': search_query,
                'output': 'json'
            }

            response = self.session.get(CRT_SH_API, params=params)
            response.raise_for_status()

            data = response.json()
            if not data:
                print(' (no results)')
                return domains

            # Extract unique domain names
            for cert in data:
                name_value = cert.get('name_value', '')
                if not name_value:
                    continue

                # Split by newlines (crt.sh returns multiple SANs)
                for domain in name_value.split('\n'):
                    domain = domain.strip()
                    if not domain:
                        continue

                    # Remove wildcard prefix
                    if domain.startswith('*.'):
                        domain = domain[2:]

                    # Verify it matches our extension
                    if domain.endswith(extension):
                        domains.add(domain)

            print(f' ({len(domains)} unique domains)')
            return domains

        except requests.exceptions.RequestException as e:
            msg = f'Error querying {extension}: {str(e)}'
            print(f' ERROR')
            self.errors.append(msg)
            return domains

    def download_saudi_domains(self) -> Set[str]:
        """Download all Saudi domains from crt.sh."""
        print('\n📥 Downloading Saudi domains from crt.sh...\n')

        total_domains = set()

        # Query each Saudi domain extension
        for extension in SAUDI_DOMAINS:
            new_domains = self.query_domain_extension(extension)
            total_domains.update(new_domains)
            time.sleep(1)  # Rate limiting - 1 second between queries

        # Also download regional domains for comparison
        print('\n📥 Downloading regional domains...\n')
        for extension in REGIONAL_DOMAINS:
            new_domains = self.query_domain_extension(extension)
            total_domains.update(new_domains)
            time.sleep(1)

        return total_domains

    def filter_saudi_domains(self, domains: Set[str]) -> Dict[str, List[str]]:
        """Filter and categorize domains by type."""
        categorized = {
            'saudi': [],
            'regional': [],
            'other': []
        }

        for domain in sorted(domains):
            if any(domain.endswith(ext) for ext in SAUDI_DOMAINS):
                categorized['saudi'].append(domain)
            elif any(domain.endswith(ext) for ext in REGIONAL_DOMAINS):
                categorized['regional'].append(domain)
            else:
                categorized['other'].append(domain)

        return categorized

    def save_results(self, domains: Set[str], categorized: Dict[str, List[str]]):
        """Save domains to text and JSON files."""
        print('\n💾 Saving results...\n')

        # Save as text (one domain per line) - saudi only
        txt_file = self.output_dir / 'saudi_domains.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            for domain in sorted(categorized['saudi']):
                f.write(f'{domain}\n')
        print(f'✓ Saved {len(categorized["saudi"])} Saudi domains to {txt_file}')

        # Save as JSON with metadata
        json_file = self.output_dir / 'saudi_domains.json'
        metadata = {
            'downloaded_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'total_domains': len(categorized['saudi']),
            'saudi_domains': sorted(categorized['saudi']),
            'regional_domains': sorted(categorized['regional']),
            'other_domains': sorted(categorized['other']),
            'source': 'Certificate Transparency logs (crt.sh)',
            'extensions': {
                'saudi': SAUDI_DOMAINS,
                'regional': REGIONAL_DOMAINS
            }
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f'✓ Saved metadata to {json_file}')

        # Save summary report
        report_file = self.output_dir / 'domains_summary.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('Saudi Company Domains - Certificate Transparency Report\n')
            f.write('=' * 60 + '\n\n')
            f.write(f'Downloaded: {metadata["downloaded_at"]}\n')
            f.write(f'Source: {metadata["source"]}\n\n')
            f.write(f'Saudi domains (.sa, .com.sa, etc): {len(categorized["saudi"])}\n')
            f.write(f'Regional domains (.ae, .co, etc): {len(categorized["regional"])}\n')
            f.write(f'Total domains found: {len(domains)}\n\n')

            if self.errors:
                f.write('Errors encountered:\n')
                for error in self.errors:
                    f.write(f'  - {error}\n')

        print(f'✓ Saved report to {report_file}')

        # Print summary
        print(f'\n📊 Summary:')
        print(f'  Saudi domains: {len(categorized["saudi"])}')
        print(f'  Regional domains: {len(categorized["regional"])}')
        print(f'  Total: {len(domains)}')

    def run(self):
        """Execute the complete download workflow."""
        start_time = time.time()

        # Download domains
        all_domains = self.download_saudi_domains()

        if not all_domains:
            print('❌ No domains found. Check your internet connection.')
            return False

        # Categorize
        categorized = self.filter_saudi_domains(all_domains)

        # Save
        self.save_results(all_domains, categorized)

        elapsed = time.time() - start_time
        print(f'\n✅ Complete! Duration: {elapsed:.1f} seconds\n')

        return True


def main():
    """Main entry point."""
    print('🔍 Saudi Domain Bulk Download from Certificate Transparency Logs\n')

    downloader = CertTransparencyDownloader()
    success = downloader.run()

    if success:
        print('Next steps:')
        print('1. Review the downloaded domains in:', downloader.output_dir)
        print('2. Create a SearXNG engine to search these domains')
        print('3. Add the engine to settings.template.yml')
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
