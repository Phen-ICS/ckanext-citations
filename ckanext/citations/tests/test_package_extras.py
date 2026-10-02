import json

from ckanext.citations.lib.package_extras import (
    get_creator_orcids,
    get_published_doi,
    get_reference_dois,
)


def _pkg(extras=None, **extra_fields):
    return {'extras': extras or [], **extra_fields}


def test_get_published_doi_requires_both_doi_and_status():
    assert get_published_doi(_pkg(doi='10.1234/x', doi_status=True)) == '10.1234/x'
    assert get_published_doi(_pkg(doi='10.1234/x', doi_status=False)) is None
    assert get_published_doi(_pkg(doi=None, doi_status=True)) is None


def test_get_creator_orcids_extracts_orcid_from_name_identifiers():
    creators = [
        {
            'name': 'Doe, Jane',
            'nameIdentifiers': [
                {
                    'nameIdentifier': 'https://orcid.org/0000-0001-2345-6789',
                    'nameIdentifierScheme': 'ORCID',
                }
            ],
        },
        {'name': 'No Orcid Author', 'nameIdentifiers': []},
    ]
    pkg = _pkg(extras=[{'key': 'datacite.creators', 'value': json.dumps(creators)}])
    assert get_creator_orcids(pkg) == [('0000-0001-2345-6789', 'Doe, Jane')]


def test_get_reference_dois_filters_by_relation_and_identifier_type():
    related = [
        {
            'relatedIdentifier': '10.1111/aaa',
            'relatedIdentifierType': 'DOI',
            'relationType': 'References',
        },
        {
            'relatedIdentifier': '10.2222/bbb',
            'relatedIdentifierType': 'DOI',
            'relationType': 'IsSupplementTo',
        },
        {
            'relatedIdentifier': 'https://example.org/not-a-doi',
            'relatedIdentifierType': 'URL',
            'relationType': 'Cites',
        },
    ]
    pkg = _pkg(
        extras=[{'key': 'datacite.relatedIdentifiers', 'value': json.dumps(related)}]
    )
    assert get_reference_dois(pkg) == ['10.1111/aaa']
