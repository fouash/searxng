# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search request monitoring and logging per hour."""

import logging
from datetime import datetime
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

class SearchMonitor:
    """Track number of searches per hour."""

    def __init__(self):
        self.searches_per_hour = defaultdict(int)
        self.lock = Lock()

    def log_search(self, query, category=None, language=None, engine=None):
        """Log a search request."""
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d %H:00')

        with self.lock:
            self.searches_per_hour[hour_key] += 1
            count = self.searches_per_hour[hour_key]

        logger.info(
            f"SEARCH [{hour_key}] #{count} | query={query[:50]} | "
            f"category={category} | language={language} | engine={engine}"
        )

        return count

    def get_hourly_stats(self):
        """Get statistics for all hours."""
        with self.lock:
            return dict(self.searches_per_hour)

    def get_current_hour_count(self):
        """Get search count for current hour."""
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d %H:00')
        return self.searches_per_hour.get(hour_key, 0)


# Global instance
search_monitor = SearchMonitor()
