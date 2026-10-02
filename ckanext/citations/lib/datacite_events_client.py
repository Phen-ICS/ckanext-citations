"""Fallback citation source: DataCite's Event Data API.

Used only to top up the citation count when OpenAlex hasn't indexed the
dataset's DOI at all. Event Data exposes bare subject/object DOI pairs, not
author/ORCID/reference-list metadata, so works discovered this way cannot
feed the disruption index or the S-index - they only contribute to
citation_count_current.
"""

import logging
import time

import requests

log = logging.getLogger(__name__)

BASE_URL = 'https://api.datacite.org/events'
REQUEST_TIMEOUT = 20
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.0


class DataciteEventsError(Exception):
    pass


def _get_with_backoff(params):
    backoff = INITIAL_BACKOFF_SECONDS
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            last_error = f'DataCite Event Data request failed: {e}'
            log.warning(
                '%s (attempt %s/%s, retrying in %.1fs)',
                last_error,
                attempt,
                MAX_RETRIES,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2.0
            continue

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429 or resp.status_code >= 500:
            last_error = (
                f'DataCite Event Data returned {resp.status_code}: {resp.text[:200]}'
            )
            log.warning(
                '%s (attempt %s/%s, retrying in %.1fs)',
                last_error,
                attempt,
                MAX_RETRIES,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2.0
            continue
        raise DataciteEventsError(
            f'DataCite Event Data returned {resp.status_code}: {resp.text[:200]}'
        )

    raise DataciteEventsError(
        f'DataCite Event Data request failed after {MAX_RETRIES} attempts: {last_error}'
    )


def get_citing_dois(doi):
    """Return the list of citing DOIs for `doi` via the is-cited-by relation.
    Returns [] if DataCite has no events for this DOI (not an error - most
    datasets simply won't have any yet)."""
    params = {
        'doi': doi,
        'relation-type-id': 'is-cited-by',
        'page[size]': 200,
    }
    data = _get_with_backoff(params)
    citing_dois = []
    for event in data.get('data', []):
        attrs = event.get('attributes', {})
        subj_id = attrs.get('subjId') or ''
        # subjId is the citing work's DOI as a URL (https://doi.org/10.xxx/yyy).
        if 'doi.org/' in subj_id:
            citing_dois.append(subj_id.split('doi.org/', 1)[-1])
    return citing_dois
