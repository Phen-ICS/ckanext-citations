import os

import pytest


def pytest_sessionstart(session):
    """Fail fast if tests are not using the isolated CKAN test config."""
    if os.environ.get('CITATIONS_ALLOW_NON_TEST_INI') == '1':
        return

    ckan_ini = getattr(session.config.option, 'ckan_ini', '') or ''
    normalized = ckan_ini.replace('\\', '/').strip()

    if normalized.endswith('/test.ini') or normalized == 'test.ini':
        return

    raise pytest.UsageError(
        'Unsafe CKAN test configuration detected. '
        'Run tests with --ckan-ini=/plugins/ckanext-citations/test.ini '
        '(or set CITATIONS_ALLOW_NON_TEST_INI=1 to bypass intentionally).'
    )
