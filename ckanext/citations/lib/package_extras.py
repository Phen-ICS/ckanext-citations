"""Small, dependency-free readers for the "datacite.*" FDF extras this
plugin needs (creators' ORCIDs, relatedIdentifiers). Deliberately not
imported from ckanext-fair3r's own rdf_extras.py so ckanext-citations stays
usable against any ckanext-doi-based dataset, not only FAIR3R/FDF ones.
"""

import json
import logging

log = logging.getLogger(__name__)


def get_extra(dataset_dict, key):
    for extra in dataset_dict.get('extras', []) or []:
        if isinstance(extra, dict) and extra.get('key') == key:
            return extra.get('value')
    return None


def get_json_extra(dataset_dict, key):
    raw = get_extra(dataset_dict, key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        log.warning("Could not parse extra '%s' as JSON", key)
        return None


def get_published_doi(dataset_dict):
    """The dataset's DOI, only once ckanext-doi has actually published it -
    a reserved-but-unpublished DOI isn't resolvable anywhere yet."""
    if dataset_dict.get('doi') and dataset_dict.get('doi_status'):
        return dataset_dict['doi']
    return None


def get_creator_orcids(dataset_dict):
    """List of (orcid, display_name) for every creator who has an ORCID
    nameIdentifier in the dataset's DataCite metadata."""
    creators = get_json_extra(dataset_dict, 'datacite.creators') or []
    result = []
    for creator in creators:
        if not isinstance(creator, dict):
            continue
        for name_id in creator.get('nameIdentifiers') or []:
            scheme = (name_id.get('nameIdentifierScheme') or '').upper()
            if scheme != 'ORCID':
                continue
            raw = name_id.get('nameIdentifier') or ''
            orcid = raw.rsplit('/', 1)[-1].strip()
            if orcid:
                result.append(
                    (orcid, creator.get('name') or creator.get('creatorName'))
                )
            break
    return result


def get_reference_dois(dataset_dict):
    """DOIs the dataset itself declares as 'References'/'Cites' related
    identifiers - used to enrich the disruption-index reference set, since
    OpenAlex rarely has a reference list for a dataset-type Work."""
    related = get_json_extra(dataset_dict, 'datacite.relatedIdentifiers') or []
    dois = []
    for item in related:
        if not isinstance(item, dict):
            continue
        if item.get('relationType') not in ('References', 'Cites'):
            continue
        if (item.get('relatedIdentifierType') or '').upper() != 'DOI':
            continue
        doi = (item.get('relatedIdentifier') or '').strip()
        if doi:
            dois.append(doi)
    return dois
