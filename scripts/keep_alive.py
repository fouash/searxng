#!/usr/bin/env python3
"""Keep Render instance alive by pinging it periodically."""

import sys
import time
from urllib.request import urlopen
from urllib.error import URLError

def ping_instance(url, timeout=10):
    """Ping the instance to keep it alive."""
    if not url:
        print("Error: No URL provided")
        return False

    # Ensure URL has proper format
    if not url.startswith('http'):
        url = f'https://{url}'

    # Ping the search endpoint (simple and always available)
    ping_url = f'{url}/search?q=test&format=json'

    try:
        start = time.time()
        response = urlopen(ping_url, timeout=timeout)
        elapsed = time.time() - start

        if response.status == 200:
            print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] ✓ Keep-alive ping successful ({elapsed:.2f}s)')
            return True
        else:
            print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] ✗ Status {response.status}')
            return False

    except URLError as e:
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] ✗ Connection failed: {e}')
        return False
    except Exception as e:
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] ✗ Error: {e}')
        return False


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 scripts/keep_alive.py <render_url>')
        print('Example: python3 scripts/keep_alive.py https://my-instance.onrender.com')
        sys.exit(1)

    render_url = sys.argv[1]
    success = ping_instance(render_url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
