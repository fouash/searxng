#!/usr/bin/env python3
"""Validate SearXNG deployment configuration before deployment."""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeploymentValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []

    def add_error(self, msg):
        self.errors.append(msg)
        logger.error(f"❌ {msg}")

    def add_warning(self, msg):
        self.warnings.append(msg)
        logger.warning(f"⚠️ {msg}")

    def add_success(self, msg):
        self.success.append(msg)
        logger.info(f"✓ {msg}")

    def check_files_exist(self):
        """Check if all required files exist."""
        logger.info("\n1. Checking required files...")

        required_files = [
            ('Dockerfile', 'Docker build configuration'),
            ('container/render-entrypoint.sh', 'Render startup script'),
            ('container/settings.template.yml', 'Settings configuration'),
            ('requirements.txt', 'Python dependencies'),
            ('searx/engines/saudi_companies_db.py', 'Saudi companies engine'),
            ('data/domains/saudi_domains.json', 'Saudi domains database'),
            ('data/domains/company_mappings.json', 'Company name mappings'),
        ]

        for file_path, description in required_files:
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size
                self.add_success(f"{description}: {size} bytes")
            else:
                self.add_error(f"{description} not found: {file_path}")

    def check_engine_files(self):
        """Check if all engine files exist."""
        logger.info("\n2. Checking engine files...")

        engines = [
            'saudi_companies_db',
            'wayback_machine',
            'common_crawl',
            'memento_archive',
            'archive_today',
            'perma_cc',
            'arquivo_pt',
            'uk_web_archive',
            'loc_archives',
        ]

        for engine in engines:
            path = Path(f'searx/engines/{engine}.py')
            if path.exists():
                self.add_success(f"Engine: {engine}")
            else:
                self.add_error(f"Engine file missing: {engine}.py")

    def check_data_validity(self):
        """Check if data files are valid JSON."""
        logger.info("\n3. Checking data file validity...")

        data_files = [
            ('data/domains/saudi_domains.json', 'Saudi domains'),
            ('data/domains/company_mappings.json', 'Company mappings'),
        ]

        for file_path, description in data_files:
            path = Path(file_path)
            if not path.exists():
                self.add_warning(f"{description} not found: {file_path}")
                continue

            try:
                with open(path) as f:
                    data = json.load(f)

                if file_path.endswith('saudi_domains.json'):
                    saudi_count = len(data.get('saudi_domains', []))
                    regional_count = len(data.get('regional_domains', []))
                    self.add_success(
                        f"{description}: {saudi_count} Saudi + {regional_count} regional domains"
                    )
                elif file_path.endswith('company_mappings.json'):
                    mapping_count = len(data.get('company_mappings', []))
                    self.add_success(f"{description}: {mapping_count} companies mapped")

            except json.JSONDecodeError as e:
                self.add_error(f"{description} is invalid JSON: {e}")
            except Exception as e:
                self.add_error(f"Error reading {description}: {e}")

    def check_settings_configuration(self):
        """Check if settings.yml has proper engine configuration."""
        logger.info("\n4. Checking settings configuration...")

        settings_path = Path('container/settings.template.yml')
        if not settings_path.exists():
            self.add_error("Settings file not found: container/settings.template.yml")
            return

        try:
            with open(settings_path) as f:
                content = f.read()

            # Check for required configurations
            configs = [
                ('use_default_settings: true', 'Default settings enabled'),
                ('- name: saudi companies', 'Saudi companies engine configured'),
                ('engine: saudi_companies_db', 'Saudi companies engine reference'),
                ('disabled: false', 'Saudi companies engine enabled'),
            ]

            for config_text, description in configs:
                if config_text in content:
                    self.add_success(description)
                else:
                    self.add_error(f"Missing configuration: {description}")

            # Check archive engines are configured (even if disabled)
            archive_engines = [
                'wayback machine',
                'common crawl',
                'memento archive',
                'archive.today',
                'perma.cc',
                'arquivo.pt',
                'uk web archive',
                'library of congress',
            ]

            for engine_name in archive_engines:
                if f"- name: {engine_name}" in content:
                    self.add_success(f"Archive engine configured: {engine_name}")
                else:
                    self.add_warning(f"Archive engine not configured: {engine_name}")

        except Exception as e:
            self.add_error(f"Error reading settings: {e}")

    def check_docker_configuration(self):
        """Check if Dockerfile is properly configured."""
        logger.info("\n5. Checking Docker configuration...")

        dockerfile_path = Path('Dockerfile')
        if not dockerfile_path.exists():
            self.add_error("Dockerfile not found")
            return

        try:
            with open(dockerfile_path) as f:
                content = f.read()

            checks = [
                ('FROM docker.io/searxng/base:searxng', 'Base image defined'),
                ('RUN chmod +x ./render-entrypoint.sh', 'Entrypoint configured'),
                ('mkdir -p ./data/domains', 'Data directory creation'),
                ('EXPOSE 8080', 'Port 8080 exposed'),
            ]

            for check_text, description in checks:
                if check_text in content:
                    self.add_success(f"Docker: {description}")
                else:
                    self.add_warning(f"Docker: Missing configuration - {description}")

            # Check for old apt-get that might cause issues
            if 'apt-get' in content:
                self.add_error("Dockerfile still contains apt-get (incompatible with Alpine)")
            else:
                self.add_success("Docker: Uses appropriate package manager")

        except Exception as e:
            self.add_error(f"Error reading Dockerfile: {e}")

    def check_entrypoint_script(self):
        """Check if entrypoint script is properly configured."""
        logger.info("\n6. Checking entrypoint script...")

        script_path = Path('container/render-entrypoint.sh')
        if not script_path.exists():
            self.add_error("Entrypoint script not found")
            return

        try:
            with open(script_path) as f:
                content = f.read()

            checks = [
                ('export GRANIAN_PORT=', 'Port configuration'),
                ('mkdir -p /usr/local/searxng/data/domains', 'Data directory setup'),
                ('python3 /usr/local/searxng/scripts/download_saudi_domains.py', 'Domain download script'),
                ('exec /usr/local/searxng/entrypoint.sh', 'Startup command'),
            ]

            for check_text, description in checks:
                if check_text in content:
                    self.add_success(f"Entrypoint: {description}")
                else:
                    self.add_warning(f"Entrypoint: Missing - {description}")

        except Exception as e:
            self.add_error(f"Error reading entrypoint: {e}")

    def check_requirements(self):
        """Check if requirements.txt has necessary packages."""
        logger.info("\n7. Checking requirements...")

        req_path = Path('requirements.txt')
        if not req_path.exists():
            self.add_error("requirements.txt not found")
            return

        try:
            with open(req_path) as f:
                content = f.read()

            packages = [
                ('httpx', 'HTTP requests library'),
                ('requests', 'HTTP client'),
                ('boto3', 'AWS/R2 S3 client (optional for R2 storage)'),
            ]

            for package, description in packages:
                if package in content:
                    self.add_success(f"Package: {description}")
                else:
                    if 'optional' in description:
                        self.add_warning(f"Package not found (optional): {description}")
                    else:
                        self.add_warning(f"Package not found: {description}")

        except Exception as e:
            self.add_error(f"Error reading requirements: {e}")

    def run_all_checks(self):
        """Run all validation checks."""
        logger.info("=" * 60)
        logger.info("SearXNG Deployment Validator")
        logger.info("=" * 60)

        self.check_files_exist()
        self.check_engine_files()
        self.check_data_validity()
        self.check_settings_configuration()
        self.check_docker_configuration()
        self.check_entrypoint_script()
        self.check_requirements()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Validation Summary")
        logger.info("=" * 60)
        logger.info(f"✓ Passed: {len(self.success)}")
        logger.info(f"⚠️ Warnings: {len(self.warnings)}")
        logger.info(f"❌ Errors: {len(self.errors)}")

        if self.errors:
            logger.info("\nDeployment Status: ❌ NOT READY")
            logger.info("Fix the errors above before deploying")
            return False
        elif self.warnings:
            logger.info("\nDeployment Status: ⚠️ READY (with warnings)")
            logger.info("Review warnings before deploying")
            return True
        else:
            logger.info("\nDeployment Status: ✓ READY")
            return True


def main():
    """Main entry point."""
    validator = DeploymentValidator()
    success = validator.run_all_checks()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
