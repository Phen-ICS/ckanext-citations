"""Fallback citation source: DataCite's Event Data API.

Used only to top up the citation count when OpenAlex hasn't indexed the
dataset's DOI at all. Event Data exposes bare subject/object DOI pairs, not
author/ORCID/reference-list metadata, so works discovered this way cannot
feed the disruption index or the S-index - they only contribute to
citation_count_current.
"""

from ckanext.citations.lib import http

BASE_URL = 'https://api.datacite.org/events'


class DataciteEventsError(Exception):
    pass


def _bare_doi(doi_url):
    """'https://doi.org/10.x/y' -> '10.x/y', lowercased (DOIs are case-
    insensitive); '' for anything that isn't a doi.org URL."""
    if 'doi.org/' not in (doi_url or ''):
        return ''
    return doi_url.split('doi.org/', 1)[-1].lower()


def get_citing_dois(doi):
    """Return the list of citing DOIs for `doi` via the is-cited-by relation.
    Returns [] if DataCite has no events for this DOI (not an error - most
    datasets simply won't have any yet).

    In an "A is-cited-by B" event, B (obj-id) is the citing work. The `doi`
    filter matches either side, so only events where A (subj-id) is this
    DOI count. Attribute names are hyphenated (subj-id, obj-id)."""
    params = {
        'doi': doi,
        'relation-type-id': 'is-cited-by',
        'page[size]': 200,
    }
    # shortcut: first page (200 events) only, paginate if a dataset ever gets more.
    data = http.get_json(BASE_URL, params, DataciteEventsError) or {}
    own = doi.lower()
    citing_dois = []
    for event in data.get('data', []):
        attrs = event.get('attributes', {})
        if _bare_doi(attrs.get('subj-id')) != own:
            continue
        citing = _bare_doi(attrs.get('obj-id'))
        if citing and citing not in citing_dois:
            citing_dois.append(citing)
    return citing_dois
