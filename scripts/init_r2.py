#!/usr/bin/env python3
"""Initialize Cloudflare R2 bucket structure for SearXNG"""

import os
import sys
import boto3

def init_r2():
    """Create folder structure in Cloudflare R2"""

    access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID')
    secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    bucket_name = os.environ.get('CLOUDFLARE_R2_BUCKET_NAME', 'searxng')
    endpoint_url = os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL')

    if not all([access_key, secret_key, endpoint_url]):
        print("ERROR: Cloudflare R2 credentials not configured")
        print("\nRequired environment variables:")
        print("  - CLOUDFLARE_R2_ACCESS_KEY_ID")
        print("  - CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        print("  - CLOUDFLARE_R2_ENDPOINT_URL")
        sys.exit(1)

    print(f"Initializing Cloudflare R2...")
    print(f"  Bucket: {bucket_name}")
    print(f"  Endpoint: {endpoint_url}")

    client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto'
    )

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

    print("\nCreating folder structure...")
    for folder in folders:
        try:
            client.put_object(
                Bucket=bucket_name,
                Key=folder + '.keep',
                Body=b'',
                ContentType='application/octet-stream'
            )
            print(f"  ✓ {folder}")
        except Exception as e:
            print(f"  ✗ {folder}: {e}")

    print("\nVerifying bucket structure...")
    try:
        response = client.list_objects_v2(Bucket=bucket_name)
        total_objects = response.get('KeyCount', 0)
        total_size = sum(obj.get('Size', 0) for obj in response.get('Contents', []))

        print(f"\n✓ Bucket initialized successfully")
        print(f"  Objects: {total_objects}")
        print(f"  Size: {total_size / 1024:.2f} KB")
        print(f"  Estimated cost: ${(total_size / (1024 * 1024 * 1024)) * 0.015:.4f}/month")

    except Exception as e:
        print(f"\nERROR: Could not verify bucket: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_r2()
