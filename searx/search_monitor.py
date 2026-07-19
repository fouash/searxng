# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search request monitoring and logging: hourly, daily, weekly."""

import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Log file path for persistent search results
SEARCH_LOG_FILE = os.environ.get('SEARXNG_LOG_DIR', '/var/log/searxng') + '/search_results.log'

class SearchMonitor:
    """Track searches with detailed metrics: results, engines, response time, errors."""

    def __init__(self, max_history=500):
        self.searches_per_hour = defaultdict(int)
        self.searches_per_day = defaultdict(int)
        self.searches_per_week = defaultdict(int)
        self.results_total = defaultdict(int)
        self.empty_results = defaultdict(int)
        self.successful_searches = defaultdict(int)
        self.failed_searches = defaultdict(int)
        self.response_times = defaultdict(list)
        self.engines_used = defaultdict(lambda: defaultdict(int))
        self.search_history = []
        self.max_history = max_history
        self.lock = Lock()
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure log file directory exists and create file if needed."""
        try:
            log_dir = os.path.dirname(SEARCH_LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            # Create file if it doesn't exist
            if not os.path.exists(SEARCH_LOG_FILE):
                with open(SEARCH_LOG_FILE, 'w') as f:
                    f.write('Timestamp | Search Query | Results Count | First Result URL | Engines | Status\n')
                    f.write('=' * 120 + '\n')
        except Exception as e:
            logger.warning(f"Could not ensure log file: {e}")

    def _write_search_log(self, timestamp, query, num_results, result_urls, engines, status):
        """Write search results to persistent log file.

        Args:
            timestamp: Search timestamp
            query: Search query
            num_results: Total number of results
            result_urls: List of result URLs (up to 10)
            engines: Engines used
            status: Search status
        """
        try:
            query_short = (query[:50] + '...') if len(query) > 50 else query

            # Write header for this search
            header = f"\n{'='*140}\n"
            header += f"[{timestamp}] Query: {query} | Results: {num_results} | Engines: {engines} | Status: {status}\n"
            header += f"{'='*140}\n"

            with open(SEARCH_LOG_FILE, 'a') as f:
                f.write(header)

                # Write up to 10 result URLs
                if result_urls:
                    for idx, url in enumerate(result_urls[:10], 1):
                        f.write(f"{idx:2}. {url}\n")
                else:
                    f.write("   (No results found)\n")

        except Exception as e:
            logger.warning(f"Could not write to search log file: {e}")

    def log_search(self, query, category=None, language=None, engine=None, num_results=0,
                   response_time=0.0, engines_list=None, error=None, first_result_url=None, result_urls=None):
        """Log a search request with detailed metrics.

        Args:
            query: Search query string
            category: Search category
            language: Search language
            engine: Deprecated, use engines_list instead
            num_results: Number of results returned
            response_time: Response time in seconds
            engines_list: List of engines that returned results (e.g., ['crtsh', 'whois'])
            error: Error message if search failed
            first_result_url: URL of the first result returned (deprecated, use result_urls)
            result_urls: List of result URLs (up to 10 will be logged)
        """
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%d %H:00')
        day_key = now.strftime('%Y-%m-%d')
        week_key = now.strftime('%Y-W%W')  # ISO week

        with self.lock:
            self.searches_per_hour[hour_key] += 1
            self.searches_per_day[day_key] += 1
            self.searches_per_week[week_key] += 1

            self.results_total[day_key] += num_results

            if num_results > 0:
                self.successful_searches[day_key] += 1
            else:
                self.empty_results[day_key] += 1

            if error:
                self.failed_searches[day_key] += 1

            self.response_times[day_key].append(response_time)

            if engines_list:
                for eng in engines_list:
                    self.engines_used[day_key][eng] += 1

            # Store search in history
            first_url = result_urls[0] if result_urls else (first_result_url or '')
            search_record = {
                'timestamp': now.isoformat(),
                'query': query or 'N/A',
                'category': category or 'general',
                'language': language or 'all',
                'num_results': num_results,
                'first_result_url': first_url,
                'result_urls': result_urls or [],
                'response_time': response_time,
                'engines': ','.join(engines_list) if engines_list else 'none',
                'status': 'OK' if not error else f'ERROR: {error[:30]}',
            }
            self.search_history.append(search_record)

            # Keep only recent searches
            if len(self.search_history) > self.max_history:
                self.search_history = self.search_history[-self.max_history:]

            hour_count = self.searches_per_hour[hour_key]
            day_count = self.searches_per_day[day_key]

        status = "OK" if not error else f"ERROR: {error[:30]}"
        engines_str = ','.join(engines_list) if engines_list else 'none'

        logger.info(
            f"SEARCH [{hour_key}] hourly:#{hour_count} daily:#{day_count} | "
            f"query={query[:40] if query else 'N/A'} | "
            f"results:{num_results} | engines:{engines_str} | time:{response_time:.2f}s | "
            f"status:{status} | category={category} | language={language}"
        )

        # Write to persistent log file
        timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')
        urls_to_log = result_urls or (([first_result_url] if first_result_url else []))
        self._write_search_log(timestamp_str, query or 'N/A', num_results, urls_to_log, engines_str, status)

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

    def get_daily_results_stats(self):
        """Get total results returned per day (last 7 days)."""
        with self.lock:
            now = datetime.now()
            last_7d = now - timedelta(days=7)
            stats = {}
            for day_key, count in sorted(self.results_total.items()):
                try:
                    day_dt = datetime.strptime(day_key, '%Y-%m-%d')
                    if day_dt > last_7d:
                        stats[day_key] = count
                except ValueError:
                    pass
            return stats

    def get_success_empty_stats(self):
        """Get successful vs empty result counts (last 7 days)."""
        with self.lock:
            now = datetime.now()
            last_7d = now - timedelta(days=7)
            stats = {}
            for day_key in sorted(self.successful_searches.keys()):
                try:
                    day_dt = datetime.strptime(day_key, '%Y-%m-%d')
                    if day_dt > last_7d:
                        stats[day_key] = {
                            'successful': self.successful_searches.get(day_key, 0),
                            'empty': self.empty_results.get(day_key, 0),
                            'failed': self.failed_searches.get(day_key, 0),
                        }
                except ValueError:
                    pass
            return stats

    def get_engine_stats(self):
        """Get which engines returned results (last 7 days)."""
        with self.lock:
            now = datetime.now()
            last_7d = now - timedelta(days=7)
            stats = {}
            for day_key, engines_dict in sorted(self.engines_used.items()):
                try:
                    day_dt = datetime.strptime(day_key, '%Y-%m-%d')
                    if day_dt > last_7d:
                        stats[day_key] = dict(engines_dict)
                except ValueError:
                    pass
            return stats

    def get_response_time_stats(self):
        """Get average response time per day (last 7 days)."""
        with self.lock:
            now = datetime.now()
            last_7d = now - timedelta(days=7)
            stats = {}
            for day_key, times in sorted(self.response_times.items()):
                try:
                    day_dt = datetime.strptime(day_key, '%Y-%m-%d')
                    if day_dt > last_7d and times:
                        avg_time = sum(times) / len(times)
                        stats[day_key] = {
                            'avg': round(avg_time, 3),
                            'min': round(min(times), 3),
                            'max': round(max(times), 3),
                            'samples': len(times),
                        }
                except ValueError:
                    pass
            return stats

    def get_search_history(self, limit=None):
        """Get recent search history (most recent first)."""
        with self.lock:
            history = list(reversed(self.search_history))
            return history[:limit] if limit else history

    def get_all_stats(self):
        """Get all statistics including quality metrics."""
        with self.lock:
            return {
                'hourly': dict(self.searches_per_hour),
                'daily': dict(self.searches_per_day),
                'weekly': dict(self.searches_per_week),
            }


# Global instance
search_monitor = SearchMonitor()
