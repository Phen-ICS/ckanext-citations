import logging
import time
from datetime import datetime, timedelta, timezone

import click
from ckan.model import Package, Session

log = logging.getLogger(__name__)

DEFAULT_MIN_AGE_DAYS = 7
DEFAULT_PAUSE_SECONDS = 0.1


def get_commands():
    return [citations]


@click.group()
def citations():
    """Citation/impact tracking commands."""


@citations.command(name='refresh')
@click.option(
    '--min-age-days',
    default=DEFAULT_MIN_AGE_DAYS,
    show_default=True,
    help='Only refresh datasets whose citation stats were last checked more '
    'than this many days ago (or never checked at all).',
)
@click.option(
    '--limit',
    default=None,
    type=int,
    help='Process at most this many datasets this run.',
)
@click.option(
    '--pause-seconds',
    default=DEFAULT_PAUSE_SECONDS,
    show_default=True,
    help='Pause between datasets, on top of the per-API-call pause already '
    'applied inside each dataset refresh.',
)
def refresh(min_age_days, limit, pause_seconds):
    """Batched, idempotent citation refresh across every published-DOI
    dataset due for a check. Safe to run on a cron - only datasets whose
    last check is older than --min-age-days (or never checked) are touched.
    """
    from ckanext.citations.lib.refresh import refresh_dataset

    package_ids = _packages_due_for_refresh(min_age_days)
    if limit:
        package_ids = package_ids[:limit]

    click.echo(f'{len(package_ids)} dataset(s) due for a citation refresh.')

    for i, package_id in enumerate(package_ids, start=1):
        try:
            refresh_dataset(package_id)
            click.echo(f'[{i}/{len(package_ids)}] refreshed {package_id}')
        except Exception:
            log.exception('Citation refresh failed for dataset %s', package_id)
            click.secho(f'[{i}/{len(package_ids)}] FAILED {package_id}', fg='red')
            Session.rollback()
        time.sleep(pause_seconds)


def _packages_due_for_refresh(min_age_days):
    """Queries ckan.model directly (not the package_search action) so this
    maintenance job sees every dataset - public or private - and doesn't
    depend on Solr being in sync."""
    from ckanext.citations.model import CitationStats

    cutoff = datetime.now(timezone.utc) - timedelta(days=min_age_days)

    already_checked_recently = {
        row.package_id
        for row in Session.query(CitationStats.package_id).filter(
            CitationStats.last_checked.isnot(None), CitationStats.last_checked > cutoff
        )
    }

    all_active_ids = [
        row.id
        for row in Session.query(Package.id).filter(
            Package.state == 'active', Package.type == 'dataset'
        )
    ]
    return [pid for pid in all_active_ids if pid not in already_checked_recently]
