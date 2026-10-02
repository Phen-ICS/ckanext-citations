"""Minimal OpenAlex REST client - just the handful of calls the refresh job
needs: resolve a DOI to a Work, list works citing a Work, and fetch a Work's
own metadata (authors/ORCID, referenced_works) for the disruption-index and
S-index calculations.

No API key needed; OpenAlex asks callers to pass a contact email ("polite
pool") for better rate limits rather than for auth.
"""

import logging
import time

import requests

log = logging.getLogger(__name__)

BASE_URL = 'https://api.openalex.org'
REQUEST_TIMEOUT = 20
PAGE_SIZE = 200
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.0


class OpenAlexError(Exception):
    """Raised when OpenAlex can't answer a request (not "DOI not found")."""


def _get(path, params, contact_email=None):
    """GET with exponential backoff on 429 (rate limit) and 5xx/network
    errors - a refresh run hits this API for every citing work of every
    reference of every dataset, so transient failures are the common case,
    not the exception."""
    params = dict(params)
    if contact_email:
        params['mailto'] = contact_email

    backoff = INITIAL_BACKOFF_SECONDS
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                f'{BASE_URL}{path}', params=params, timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as e:
            last_error = f'OpenAlex request failed: {e}'
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
        if resp.status_code == 404:
            return None
        if resp.status_code == 429 or resp.status_code >= 500:
            last_error = f'OpenAlex returned {resp.status_code}: {resp.text[:200]}'
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
        raise OpenAlexError(f'OpenAlex returned {resp.status_code}: {resp.text[:200]}')

    raise OpenAlexError(
        f'OpenAlex request failed after {MAX_RETRIES} attempts: {last_error}'
    )


def resolve_doi_to_work_id(doi, contact_email=None):
    """Return the bare OpenAlex work id ("W123...") for a DOI, or None if
    OpenAlex doesn't know about it (e.g. a freshly-minted dataset DOI it
    hasn't crawled yet)."""
    data = _get(f'/works/doi:{doi}', {}, contact_email=contact_email)
    if not data:
        return None
    return _short_id(data.get('id'))


def get_work(work_id, contact_email=None):
    """Fetch one Work's metadata: authors (with ORCID), referenced_works,
    cited_by_count. Returns None if the work id is unknown."""
    data = _get(f'/works/{work_id}', {}, contact_email=contact_email)
    if not data:
        return None
    return _parse_work(data)


def iter_citing_works(work_id, contact_email=None, pause_seconds=0.1):
    """Yield every Work that cites `work_id`, paginated via OpenAlex's cursor
    pagination. Each item is the dict shape returned by _parse_work."""
    cursor = '*'
    while cursor:
        data = _get(
            '/works',
            {'filter': f'cites:{work_id}', 'per-page': PAGE_SIZE, 'cursor': cursor},
            contact_email=contact_email,
        )
        if not data:
            return
        for item in data.get('results', []):
            yield _parse_work(item)
        cursor = (data.get('meta') or {}).get('next_cursor')
        if cursor:
            time.sleep(pause_seconds)


def _short_id(openalex_url_id):
    """OpenAlex ids come back as full URLs (https://openalex.org/W123...);
    we store/compare just the "W123..." part."""
    if not openalex_url_id:
        return None
    return openalex_url_id.rsplit('/', 1)[-1]


def _parse_work(data):
    authors = []
    for authorship in data.get('authorships') or []:
        author = authorship.get('author') or {}
        orcid = author.get('orcid')
        if orcid:
            # OpenAlex returns a full URL; keep just the bare ORCID.
            orcid = orcid.rsplit('/', 1)[-1]
        authors.append({'name': author.get('display_name'), 'orcid': orcid})

    primary_location = data.get('primary_location') or {}
    source = primary_location.get('source') or {}

    doi = data.get('doi')
    if doi:
        doi = doi.replace('https://doi.org/', '')

    return {
        'openalex_work_id': _short_id(data.get('id')),
        'doi': doi,
        'title': data.get('title'),
        'year': data.get('publication_year'),
        'venue': source.get('display_name'),
        'authors': authors,
        'cited_by_count': data.get('cited_by_count'),
        'referenced_work_ids': [
            _short_id(ref) for ref in (data.get('referenced_works') or [])
        ],
    }
