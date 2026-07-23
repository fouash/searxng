#!/usr/bin/env python3
"""Direct test of engine code without importing full searx module."""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_saudi_domains_data():
    """Test if Saudi domains data is valid."""
    logger.info("Testing Saudi domains data file...")

    db_path = Path('/home/user/searxng/data/domains/saudi_domains.json')

    if not db_path.exists():
        logger.error(f"❌ File not found: {db_path}")
        return False

    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        saudi_domains = data.get('saudi_domains', [])
        regional_domains = data.get('regional_domains', [])

        logger.info(f"✓ Saudi domains: {len(saudi_domains)}")
        logger.info(f"✓ Regional domains: {len(regional_domains)}")
        logger.info(f"✓ Downloaded at: {data.get('downloaded_at')}")

        # Sample some domains
        if saudi_domains:
            logger.info(f"  Sample Saudi domains:")
            for domain in saudi_domains[:3]:
                logger.info(f"    - {domain}")

        return True

    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        return False


def test_company_mappings_data():
    """Test if company mappings data is valid."""
    logger.info("\nTesting company mappings data file...")

    mapping_path = Path('/home/user/searxng/data/domains/company_mappings.json')

    if not mapping_path.exists():
        logger.warning(f"⚠ File not found: {mapping_path} (optional)")
        return True

    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        mappings = data.get('company_mappings', [])
        logger.info(f"✓ Company mappings: {len(mappings)} entries")

        if mappings:
            logger.info(f"  Sample mappings:")
            for company in mappings[:2]:
                ar_names = company.get('ar_names', [])
                en_names = company.get('en_names', [])
                keyword = company.get('domain_keyword', '')
                logger.info(f"    - EN: {en_names} | AR: {ar_names} | Keyword: {keyword}")

        return True

    except Exception as e:
        logger.error(f"❌ Error loading mappings: {e}")
        return False


def test_engine_files_exist():
    """Test if all engine files exist."""
    logger.info("\nTesting engine files...")

    engines_path = Path('/home/user/searxng/searx/engines')
    engine_files = [
        'saudi_companies_db.py',
        'wayback_machine.py',
        'common_crawl.py',
        'memento_archive.py',
        'archive_today.py',
        'perma_cc.py',
        'arquivo_pt.py',
        'uk_web_archive.py',
        'loc_archives.py',
    ]

    for engine_file in engine_files:
        path = engines_path / engine_file
        if path.exists():
            size = path.stat().st_size
            logger.info(f"✓ {engine_file}: {size} bytes")
        else:
            logger.error(f"❌ {engine_file}: NOT FOUND")


def test_settings_config():
    """Test if settings.yml has proper engine configuration."""
    logger.info("\nTesting settings configuration...")

    settings_path = Path('/home/user/searxng/container/settings.template.yml')

    if not settings_path.exists():
        logger.error(f"❌ Settings file not found: {settings_path}")
        return False

    try:
        with open(settings_path, 'r') as f:
            content = f.read()

        # Check for engine configurations
        engines_to_check = [
            ('saudi companies', 'saudi_companies_db'),
            ('wayback machine', 'wayback_machine'),
            ('common crawl', 'common_crawl'),
            ('memento archive', 'memento_archive'),
            ('archive.today', 'archive_today'),
            ('perma.cc', 'perma_cc'),
            ('arquivo.pt', 'arquivo_pt'),
            ('uk web archive', 'uk_web_archive'),
            ('library of congress', 'loc_archives'),
        ]

        logger.info("Engine configurations found:")
        for engine_name, engine_type in engines_to_check:
            if f"- name: {engine_name}" in content and f"engine: {engine_type}" in content:
                logger.info(f"✓ {engine_name}")
            else:
                logger.warning(f"⚠ {engine_name}: Not properly configured")

        return True

    except Exception as e:
        logger.error(f"❌ Error reading settings: {e}")
        return False


def main():
    """Run all diagnostic tests."""
    logger.info("=" * 60)
    logger.info("SearXNG Data & Engine Diagnostic")
    logger.info("=" * 60 + "\n")

    test_saudi_domains_data()
    test_company_mappings_data()
    test_engine_files_exist()
    test_settings_config()

    logger.info("\n" + "=" * 60)
    logger.info("Diagnostic complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
