#!/usr/bin/env python3
"""Test SearXNG API to diagnose search issues."""

import sys
import json
import logging
from urllib.parse import urljoin
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearXNGTester:
    def __init__(self, base_url='http://localhost:8080'):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def test_connection(self):
        """Test if SearXNG is accessible."""
        logger.info(f"Testing connection to {self.base_url}...")
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                logger.info("✓ SearXNG is accessible")
                return True
            else:
                logger.error(f"❌ SearXNG returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to {self.base_url}")
            logger.info("   Make sure SearXNG is running: docker run -p 8080:8080 ...")
            return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False

    def test_search(self, query, engines=None, format='json'):
        """Test a search query."""
        params = {'q': query, 'format': format}
        if engines:
            params['engines'] = engines

        logger.info(f"\nSearching for: '{query}'")
        if engines:
            logger.info(f"Engines: {engines}")

        try:
            response = self.session.get(
                f"{self.base_url}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            if format == 'json':
                data = response.json()
                results = data.get('results', [])
                logger.info(f"✓ Found {len(results)} results")

                if results:
                    logger.info("  First 3 results:")
                    for i, result in enumerate(results[:3], 1):
                        title = result.get('title', 'No title')
                        url = result.get('url', 'No URL')
                        engine = result.get('engine', 'unknown')
                        logger.info(f"    {i}. [{engine}] {title}")
                        logger.info(f"       URL: {url}")
                else:
                    logger.warning("  No results returned")

                return results

            else:
                logger.info(f"✓ Response status: {response.status_code}")
                return response.text

        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []

    def test_saudi_engine(self):
        """Test the Saudi companies engine specifically."""
        logger.info("\n" + "=" * 60)
        logger.info("Testing Saudi Companies Engine")
        logger.info("=" * 60)

        # Test queries that should match domains
        test_queries = [
            'mobily',      # Should find mobily.com.sa
            'aramco',      # Should find aramco domains
            'stc',         # Should find telecom domains
            'saudi',       # Should find saudi domains
            'random123',   # Should find nothing
        ]

        for query in test_queries:
            results = self.test_search(query, engines='saudi_companies')
            # Small delay between requests
            import time
            time.sleep(0.5)

    def test_archive_engines(self):
        """Test archive engines."""
        logger.info("\n" + "=" * 60)
        logger.info("Testing Archive Engines (may be disabled)")
        logger.info("=" * 60)

        engines = ['wayback_machine', 'common_crawl', 'memento_archive']
        query = 'wikipedia'

        for engine in engines:
            results = self.test_search(query, engines=engine)
            import time
            time.sleep(0.5)

    def test_all_engines(self):
        """Test with all engines enabled."""
        logger.info("\n" + "=" * 60)
        logger.info("Testing All Engines (Summary)")
        logger.info("=" * 60)

        results = self.test_search('aramco')
        if results:
            # Group by engine
            by_engine = {}
            for result in results:
                engine = result.get('engine', 'unknown')
                by_engine.setdefault(engine, []).append(result)

            logger.info("\nResults by engine:")
            for engine, items in by_engine.items():
                logger.info(f"  {engine}: {len(items)} results")

    def check_engine_configuration(self):
        """Check which engines are enabled."""
        logger.info("\n" + "=" * 60)
        logger.info("Checking Engine Configuration")
        logger.info("=" * 60)

        settings_path = Path('container/settings.template.yml')
        if not settings_path.exists():
            logger.warning("Settings file not found")
            return

        with open(settings_path) as f:
            content = f.read()

        engines_to_check = [
            'saudi companies',
            'wayback machine',
            'common crawl',
            'memento archive',
        ]

        for engine_name in engines_to_check:
            enabled = f"- name: {engine_name}" in content and \
                     f"disabled: false" in content.split(f"- name: {engine_name}")[1].split("- name:")[0]
            status = "✓ Enabled" if enabled else "✗ Disabled"
            logger.info(f"{status}: {engine_name}")

    def run_full_diagnostic(self):
        """Run full diagnostic suite."""
        logger.info("=" * 60)
        logger.info("SearXNG Full Diagnostic")
        logger.info("=" * 60 + "\n")

        if not self.test_connection():
            return

        self.check_engine_configuration()
        self.test_saudi_engine()
        self.test_all_engines()

        logger.info("\n" + "=" * 60)
        logger.info("Diagnostic Complete!")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Test SearXNG deployment')
    parser.add_argument('--url', default='http://localhost:8080', help='SearXNG base URL')
    parser.add_argument('--query', help='Test specific query')
    parser.add_argument('--engine', help='Test specific engine')
    parser.add_argument('--full', action='store_true', help='Run full diagnostic')

    args = parser.parse_args()

    tester = SearXNGTester(args.url)

    if args.full:
        tester.run_full_diagnostic()
    elif args.query:
        tester.test_search(args.query, engines=args.engine)
    else:
        if tester.test_connection():
            tester.check_engine_configuration()
            logger.info("\nRun with --full for complete diagnostic")
            logger.info("Run with --query '<text>' to test a search")
            logger.info("Run with --query '<text>' --engine '<engine>' to test specific engine")


if __name__ == '__main__':
    main()
