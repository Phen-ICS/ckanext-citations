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


@pytest.fixture
def citations_tables():
    """Create this plugin's tables in the test DB. The Alembic migration is
    what creates them in a real environment; tests only need the schema, and
    create_all(checkfirst=True) is idempotent."""
    from ckan.model import meta

    from ckanext.citations import model

    meta.metadata.create_all(
        bind=meta.engine,
        tables=[
            model.citation_stats_table,
            model.citing_work_table,
            model.citing_researcher_table,
            model.author_sindex_table,
            model.score_history_table,
        ],
        checkfirst=True,
    )
