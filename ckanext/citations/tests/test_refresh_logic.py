import pytest
from ckan.model import Session
from ckan.tests import factories

from ckanext.citations.lib import refresh
from ckanext.citations.model import CitingWork

pytestmark = pytest.mark.usefixtures('citations_tables')


def _work(openalex_id, doi=None):
    return {
        'openalex_work_id': openalex_id,
        'doi': doi,
        'title': f'Work {openalex_id}',
        'authors': [],
        'year': 2024,
        'venue': 'Journal',
        'referenced_work_ids': [],
        'cited_by_count': 0,
    }


@pytest.mark.usefixtures('clean_db')
def test_citing_works_without_doi_are_not_merged(monkeypatch):
    dataset = factories.Dataset()
    monkeypatch.setattr(refresh, 'get_published_doi', lambda pkg: '10.1234/fake')
    monkeypatch.setattr(
        refresh.openalex_client, 'resolve_doi_to_work_id', lambda doi, email=None: 'W1'
    )
    monkeypatch.setattr(
        refresh.openalex_client,
        'get_work',
        lambda work_id, email=None: {'referenced_work_ids': []},
    )
    monkeypatch.setattr(
        refresh.openalex_client,
        'iter_citing_works',
        lambda work_id, email=None, pause_seconds=0.1, max_items=None: iter(
            [_work('W10'), _work('W11')]
        ),
    )

    refresh.refresh_dataset(dataset['id'])

    rows = Session.query(CitingWork).filter_by(package_id=dataset['id']).all()
    assert sorted(r.openalex_work_id for r in rows) == ['W10', 'W11']


@pytest.mark.usefixtures('clean_db')
def test_openalex_work_id_is_resolved_on_every_refresh(monkeypatch):
    dataset = factories.Dataset()
    calls = []
    monkeypatch.setattr(refresh, 'get_published_doi', lambda pkg: '10.1234/fake')

    def resolve(doi, email=None):
        calls.append(doi)
        return 'W1'

    monkeypatch.setattr(refresh.openalex_client, 'resolve_doi_to_work_id', resolve)
    monkeypatch.setattr(
        refresh.openalex_client,
        'get_work',
        lambda work_id, email=None: {'referenced_work_ids': []},
    )
    monkeypatch.setattr(
        refresh.openalex_client,
        'iter_citing_works',
        lambda work_id, email=None, pause_seconds=0.1, max_items=None: iter([]),
    )

    refresh.refresh_dataset(dataset['id'])
    refresh.refresh_dataset(dataset['id'])

    assert len(calls) == 2
