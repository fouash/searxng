#!/usr/bin/env python3
"""
Keep Render instance alive by pinging it periodically.
Prevents free tier spin-down after 15 minutes of inactivity.

Usage:
    python3 scripts/keep_alive.py https://your-render-instance.onrender.com

Or set up as cron job:
    */10 * * * * cd /path/to/searxng && python3 scripts/keep_alive.py https://your-render-instance.onrender.com >> logs/keep_alive.log 2>&1
"""

import sys
import time
import logging
from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ping_instance(url, timeout=10):
    """Ping the Render instance to keep it alive."""
    if not url:
        logger.error("No URL provided")
        return False

    # Ensure URL has proper format
    if not url.startswith('http'):
        url = f'https://{url}'

    # Add keep-alive endpoint
    ping_url = f'{url}/keep-alive'

    try:
        logger.info(f'Pinging {ping_url}...')
        start = time.time()
        response = urlopen(ping_url, timeout=timeout)
        elapsed = time.time() - start

        if response.status == 200:
            logger.info(f'✓ Success ({elapsed:.2f}s) - Instance alive')
            return True
        else:
            logger.warning(f'✗ Status {response.status}')
            return False

    except URLError as e:
        logger.error(f'✗ Connection failed: {e}')
        return False
    except Exception as e:
        logger.error(f'✗ Error: {e}')
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error('Usage: python3 scripts/keep_alive.py <render_url>')
        logger.error('Example: python3 scripts/keep_alive.py https://my-instance.onrender.com')
        sys.exit(1)

    render_url = sys.argv[1]
    success = ping_instance(render_url)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
