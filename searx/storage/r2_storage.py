"""Cloudflare R2 storage backend for SearXNG stats and archives"""

import os
import json
import gzip
import hashlib
import boto3
from datetime import datetime
from io import BytesIO


class R2Storage:
    """Cloudflare R2 storage client for persistent data"""

    def __init__(self):
        self.access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID')
        self.secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.environ.get('CLOUDFLARE_R2_BUCKET_NAME', 'searxng')
        self.endpoint_url = os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL')

        if not all([self.access_key, self.secret_key, self.endpoint_url]):
            raise ValueError("Cloudflare R2 credentials not configured")

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='auto'
        )

    def create_folders(self):
        """Create folder structure in R2"""

        folders = [
            'stats/',
            'stats/daily/',
            'stats/monthly/',
            'stats/yearly/',
            'archive/',
            'archive/pages/',
            'archive/metadata/',
            'archive/index/',
            'backups/',
            'backups/database/',
            'backups/config/',
            'logs/',
        ]

        for folder in folders:
            try:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder + '.keep',
                    Body=b'',
                    ContentType='application/octet-stream'
                )
            except Exception as e:
                print(f"Error creating folder {folder}: {e}")

    def save_stats(self, stats_data, timestamp=None):
        """Save stats snapshot to R2"""

        if timestamp is None:
            timestamp = datetime.utcnow()

        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H-%M-%S')

        key = f"stats/daily/{date_str}/{time_str}.json"

        data = {
            'timestamp': timestamp.isoformat(),
            'stats': stats_data
        }

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2).encode('utf-8'),
            ContentType='application/json'
        )

        return key

    def save_archive_page(self, url, html_content, metadata=None):
        """Save archived page to R2 (gzip compressed)"""

        timestamp = datetime.utcnow()

        hash_val = hashlib.md5(url.encode()).hexdigest()
        date_path = timestamp.strftime('%Y/%m/%d')
        key = f"archive/pages/{date_path}/{hash_val}.html.gz"

        compressed = gzip.compress(html_content.encode('utf-8'))

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=compressed,
            ContentType='text/html',
            ContentEncoding='gzip',
            Metadata={
                'original-url': url,
                'archived-timestamp': timestamp.isoformat()
            }
        )

        meta_key = f"archive/metadata/{date_path}/{hash_val}.json"
        meta = {
            'url': url,
            'archived': timestamp.isoformat(),
            'size': len(html_content),
            'compressed_size': len(compressed),
            'storage_key': key,
            **(metadata or {})
        }

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=meta_key,
            Body=json.dumps(meta).encode('utf-8'),
            ContentType='application/json'
        )

        return key

    def get_daily_stats(self, date_str):
        """Retrieve all stats for a day (YYYY-MM-DD)"""

        prefix = f"stats/daily/{date_str}/"

        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        stats = []
        for obj in response.get('Contents', []):
            resp = self.client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
            data = json.loads(resp['Body'].read())
            stats.append(data)

        return sorted(stats, key=lambda x: x['timestamp'])

    def get_monthly_stats(self, year_month):
        """Retrieve stats for a month (YYYY-MM)"""

        prefix = f"stats/daily/{year_month}/"

        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        all_stats = []
        for obj in response.get('Contents', []):
            resp = self.client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
            data = json.loads(resp['Body'].read())
            all_stats.append(data)

        return all_stats

    def get_archive_page(self, hash_val):
        """Retrieve archived page by hash"""

        prefix = f"archive/pages/"

        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        for obj in response.get('Contents', []):
            if hash_val in obj['Key']:
                resp = self.client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                compressed = resp['Body'].read()
                return gzip.decompress(compressed).decode('utf-8')

        return None

    def backup_database(self, db_path):
        """Backup SQLite database to R2"""

        timestamp = datetime.utcnow()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H-%M-%S')

        key = f"backups/database/{date_str}/stats_{time_str}.db"

        with open(db_path, 'rb') as f:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=f.read(),
                ContentType='application/octet-stream'
            )

        return key

    def list_all_stats(self):
        """List all stats snapshots in R2"""

        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix='stats/daily/'
        )

        return [obj['Key'] for obj in response.get('Contents', [])]

    def get_storage_stats(self):
        """Get R2 storage usage statistics"""

        response = self.client.list_objects_v2(
            Bucket=self.bucket_name
        )

        total_size = 0
        total_objects = 0

        for obj in response.get('Contents', []):
            total_size += obj['Size']
            total_objects += 1

        return {
            'total_objects': total_objects,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
        }
