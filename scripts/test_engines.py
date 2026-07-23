#!/usr/bin/env python3
"""Diagnostic tool to test SearXNG engines without running the full server."""

import sys
import logging
from pathlib import Path

# Add searx module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_saudi_companies_engine():
    """Test the Saudi companies database engine."""
    logger.info("Testing saudi_companies_db engine...")

    try:
        from searx.engines import saudi_companies_db

        # Check if database can be loaded
        domains_db = saudi_companies_db._get_domains()
        if not domains_db:
            logger.error("❌ Failed to load domains database")
            return False

        saudi_count = len(domains_db.get('saudi', set()))
        regional_count = len(domains_db.get('regional', set()))
        logger.info(f"✓ Loaded {saudi_count} Saudi domains, {regional_count} regional domains")

        # Test search with a sample query
        test_queries = ['mobily', 'aramco', 'stc', 'test']

        for query in test_queries:
            params = {'q': query}

            # Simulate request
            params = saudi_companies_db.request(params)
            logger.info(f"  Query '{query}': params={params}")

            # Simulate response (create a mock response object)
            class MockResponse:
                def __init__(self, params):
                    self.params = params
                def get(self, key, default=None):
                    return self.params.get(key, default)

            mock_resp = MockResponse(params)
            results = saudi_companies_db.response(mock_resp)
            logger.info(f"    Found {len(results)} results")
            if results:
                logger.info(f"    First result: {results[0].get('title')}")

        return True

    except Exception as e:
        logger.error(f"❌ Error testing saudi_companies_db: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_archive_engines():
    """Test archive engines for proper configuration."""
    logger.info("\nTesting archive engines...")

    archive_engines = [
        'wayback_machine',
        'common_crawl',
        'memento_archive',
        'archive_today',
        'perma_cc',
        'arquivo_pt',
        'uk_web_archive',
        'loc_archives',
    ]

    for engine_name in archive_engines:
        try:
            module_name = f'searx.engines.{engine_name}'
            __import__(module_name)
            engine_module = sys.modules[module_name]

            # Check required attributes
            required = ['request', 'response', 'about', 'paging', 'categories']
            missing = [attr for attr in required if not hasattr(engine_module, attr)]

            if missing:
                logger.warning(f"  {engine_name}: Missing attributes: {missing}")
            else:
                logger.info(f"  ✓ {engine_name}: OK")

        except ImportError as e:
            logger.error(f"  ❌ {engine_name}: Failed to import - {e}")
        except Exception as e:
            logger.error(f"  ❌ {engine_name}: Error - {e}")


def test_data_files():
    """Check if data files exist and are readable."""
    logger.info("\nChecking data files...")

    data_paths = [
        Path('/home/user/searxng/data/domains/saudi_domains.json'),
        Path('/home/user/searxng/data/domains/company_mappings.json'),
    ]

    for path in data_paths:
        if path.exists():
            try:
                import json
                with open(path) as f:
                    data = json.load(f)
                logger.info(f"  ✓ {path.name}: {len(str(data))} bytes")
            except Exception as e:
                logger.error(f"  ❌ {path.name}: Error reading - {e}")
        else:
            logger.warning(f"  ⚠ {path.name}: Not found")


def main():
    """Run all diagnostic tests."""
    logger.info("=" * 60)
    logger.info("SearXNG Engine Diagnostic Tool")
    logger.info("=" * 60 + "\n")

    test_data_files()
    test_saudi_companies_engine()
    test_archive_engines()

    logger.info("\n" + "=" * 60)
    logger.info("Diagnostic complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
