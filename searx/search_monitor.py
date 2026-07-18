# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search request monitoring and logging: hourly, daily, weekly."""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

class SearchMonitor:
    """Track number of searches per hour, day, and week."""

    def __init__(self):
        self.searches_per_hour = defaultdict(int)
        self.searches_per_day = defaultdict(int)
        self.searches_per_week = defaultdict(int)
        self.lock = Lock()

    def log_search(self, query, category=None, language=None, engine=None):
        """Log a search request."""
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d %H:00')
        day_key = now.strftime('%Y-%m-%d')
        week_key = now.strftime('%Y-W%W')  # ISO week

        with self.lock:
            self.searches_per_hour[hour_key] += 1
            self.searches_per_day[day_key] += 1
            self.searches_per_week[week_key] += 1

            hour_count = self.searches_per_hour[hour_key]
            day_count = self.searches_per_day[day_key]

        logger.info(
            f"SEARCH [{hour_key}] hourly:#{hour_count} daily:#{day_count} | "
            f"query={query[:50] if query else 'N/A'} | "
            f"category={category} | language={language}"
        )

        return hour_count

    def get_hourly_stats(self):
        """Get statistics for all hours (last 24h)."""
        with self.lock:
            now = datetime.now()
            last_24h = now - timedelta(hours=24)

            stats = {}
            for hour_key, count in sorted(self.searches_per_hour.items()):
                try:
                    hour_dt = datetime.strptime(hour_key, '%Y-%m-%d %H:%M')
                    if hour_dt > last_24h:
                        stats[hour_key] = count
                except ValueError:
                    pass
            return stats

    def get_daily_stats(self):
        """Get statistics for all days (last 7 days)."""
        with self.lock:
            now = datetime.now()
            last_7d = now - timedelta(days=7)

            stats = {}
            for day_key, count in sorted(self.searches_per_day.items()):
                try:
                    day_dt = datetime.strptime(day_key, '%Y-%m-%d')
                    if day_dt > last_7d:
                        stats[day_key] = count
                except ValueError:
                    pass
            return stats

    def get_weekly_stats(self):
        """Get statistics for all weeks (52 weeks)."""
        with self.lock:
            return dict(sorted(self.searches_per_week.items()))

    def get_current_hour_count(self):
        """Get search count for current hour."""
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d %H:00')
        return self.searches_per_hour.get(hour_key, 0)

    def get_current_day_count(self):
        """Get search count for current day."""
        now = datetime.now()
        day_key = now.strftime('%Y-%m-%d')
        return self.searches_per_day.get(day_key, 0)

    def get_current_week_count(self):
        """Get search count for current week."""
        now = datetime.now()
        week_key = now.strftime('%Y-W%W')
        return self.searches_per_week.get(week_key, 0)

    def get_all_stats(self):
        """Get all statistics."""
        with self.lock:
            return {
                'hourly': dict(self.searches_per_hour),
                'daily': dict(self.searches_per_day),
                'weekly': dict(self.searches_per_week),
            }


# Global instance
search_monitor = SearchMonitor()
