"""Minimal OpenAlex REST client - just the handful of calls the refresh job
needs: resolve a DOI to a Work, list works citing a Work, and fetch a Work's
own metadata (authors/ORCID, referenced_works) for the disruption-index and
S-index calculations.

No API key needed; OpenAlex asks callers to pass a contact email ("polite
pool") for better rate limits rather than for auth.
"""

import time

from ckanext.citations.lib import http

BASE_URL = 'https://api.openalex.org'
PAGE_SIZE = 200


class OpenAlexError(Exception):
    """Raised when OpenAlex can't answer a request (not "DOI not found")."""


def _get(path, params, contact_email=None):
    params = dict(params)
    if contact_email:
        params['mailto'] = contact_email
    return http.get_json(f'{BASE_URL}{path}', params, OpenAlexError)


def resolve_doi_to_work_id(doi, contact_email=None):
    """Return the bare OpenAlex work id ("W123...") for a DOI, or None if
    OpenAlex doesn't know about it.

    One DOI can have several OpenAlex records (e.g. an article and a dataset
    record sharing the same references). The one with the most citations is
    the one that carries the citation signal, so it wins.
    """
    data = _get(
        '/works',
        {'filter': f'doi:{doi}', 'per-page': 10, 'select': 'id,cited_by_count'},
        contact_email=contact_email,
    )
    records = (data or {}).get('results') or []
    if not records:
        return None
    best = max(records, key=lambda r: r.get('cited_by_count') or 0)
    return _short_id(best.get('id'))


def get_work(work_id, contact_email=None):
    """Fetch one Work's metadata: authors (with ORCID), referenced_works,
    cited_by_count. Returns None if the work id is unknown."""
    data = _get(f'/works/{work_id}', {}, contact_email=contact_email)
    if not data:
        return None
    return _parse_work(data)


def iter_citing_works(work_id, contact_email=None, pause_seconds=0.1, max_items=None):
    """Yield the Works that cite `work_id`, paginated via OpenAlex's cursor
    pagination. Each item is the dict shape returned by _parse_work. Stops after
    `max_items` when given."""
    cursor = '*'
    yielded = 0
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
            yielded += 1
            if max_items is not None and yielded >= max_items:
                return
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
