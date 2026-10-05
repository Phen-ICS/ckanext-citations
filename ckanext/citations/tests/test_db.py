"""Tests that need a running CKAN (plugin loading, DB writes, the CLI and the
dataset-page panel). The pure formula tests live in test_scoring.py and
test_package_extras.py and need no CKAN at all."""

import pytest
from ckan.model import Session
from ckan.tests import factories
from ckan.tests.helpers import call_action
from click.testing import CliRunner

from ckanext.citations import model
from ckanext.citations.cli import citations as citations_cli
from ckanext.citations.lib import refresh

pytestmark = pytest.mark.usefixtures('citations_tables')


def _creators_extra(creators):
    import json

    return [{'key': 'datacite.creators', 'value': json.dumps(creators)}]


def _creator(name, orcid):
    return {
        'name': name,
        'nameIdentifiers': [
            {
                'nameIdentifier': f'https://orcid.org/{orcid}',
                'nameIdentifierScheme': 'ORCID',
            }
        ],
    }


@pytest.mark.usefixtures('clean_db')
def test_refresh_skips_dataset_without_published_doi():
    dataset = factories.Dataset()

    refresh.refresh_dataset(dataset['id'])

    assert Session.get(model.CitationStats, dataset['id']) is None


@pytest.mark.usefixtures('clean_db')
def test_refresh_fallback_writes_citation_count(monkeypatch):
    dataset = factories.Dataset()
    monkeypatch.setattr(refresh, 'get_published_doi', lambda pkg: '10.1234/fake')
    monkeypatch.setattr(
        refresh.openalex_client, 'resolve_doi_to_work_id', lambda doi, email=None: None
    )
    monkeypatch.setattr(
        refresh.datacite_events_client,
        'get_citing_dois',
        lambda doi: ['10.1/a', '10.1/b', '10.1/c'],
    )

    refresh.refresh_dataset(dataset['id'])

    stats = Session.get(model.CitationStats, dataset['id'])
    assert stats.citation_count_current == 3
    assert stats.citation_count_max == 3
    assert stats.disruption_index is None
    assert stats.last_checked is not None


@pytest.mark.usefixtures('clean_db')
def test_sindex_deduplicates_citing_researchers_across_datasets():
    """Core S-index rule: a citing researcher who cites two different datasets
    of the same author must be counted once."""
    author_orcid = '0000-0001-0000-0001'
    shared_citer = {'name': 'Shared Citer', 'orcid': '0000-0002-0000-0009'}
    other_citer = {'name': 'Other Citer', 'orcid': '0000-0002-0000-0010'}

    ds1 = factories.Dataset()
    ds2 = factories.Dataset()
    for ds, citers in (
        (ds1, [shared_citer]),
        (ds2, [shared_citer, other_citer]),
    ):
        pkg = dict(ds)
        pkg['extras'] = _creators_extra([_creator('Doe, Jane', author_orcid)])
        citing_works = [{'authors': citers}]
        refresh._update_sindex_contributions(pkg, citing_works, now=_now())

    Session.commit()
    author = Session.get(model.AuthorSIndex, author_orcid)
    assert author.s_index_current == 2
    assert author.s_index_max == 2


@pytest.mark.usefixtures('clean_db')
def test_panel_renders_on_dataset_page(app):
    dataset = factories.Dataset(private=False)
    Session.add(
        model.CitationStats(
            package_id=dataset['id'],
            citation_count_current=4,
            citation_count_max=4,
            disruption_index=0.25,
            last_checked=_now(),
        )
    )
    Session.commit()

    response = app.get(f'/dataset/{dataset["name"]}')

    assert response.status_code == 200
    assert 'id="citations-panel"' in response.body
    assert 'Disruption index' in response.body


@pytest.mark.usefixtures('clean_db')
def test_cli_refresh_runs_on_empty_catalog():
    result = CliRunner().invoke(citations_cli, ['refresh', '--limit', '5'])

    assert result.exit_code == 0, result.output


@pytest.mark.usefixtures('clean_db')
def test_package_show_still_works_with_plugin_enabled():
    dataset = factories.Dataset()
    pkg = call_action('package_show', id=dataset['id'])
    assert pkg['id'] == dataset['id']


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)
