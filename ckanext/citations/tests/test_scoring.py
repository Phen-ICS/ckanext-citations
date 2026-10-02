"""Pure formula tests - no DB, no network. These are the numbers the whole
feature depends on, so they're worth pinning down precisely."""

from ckanext.citations.lib.scoring import (
    citing_person_key,
    classify_citing_work,
    disruption_index,
)


def test_disruption_index_fully_disruptive():
    # Every citing work is "fresh" (none also cite the dataset's references).
    assert disruption_index(n_fresh=10, n_building=0, n_reference_only=0) == 1.0


def test_disruption_index_fully_developmental():
    # Every citing work also cites the dataset's references, and nothing
    # cites only the references.
    assert disruption_index(n_fresh=0, n_building=10, n_reference_only=0) == -1.0


def test_disruption_index_mixed():
    # DI = (6 - 2) / (6 + 2 + 2) = 0.4
    assert disruption_index(n_fresh=6, n_building=2, n_reference_only=2) == 0.4


def test_disruption_index_no_data_yet():
    assert disruption_index(0, 0, 0) is None


def test_classify_citing_work_building_when_references_overlap():
    cls = classify_citing_work(
        citing_referenced_work_ids=['W1', 'W2'], dataset_reference_work_ids={'W2', 'W9'}
    )
    assert cls == 'building'


def test_classify_citing_work_fresh_when_no_overlap():
    cls = classify_citing_work(
        citing_referenced_work_ids=['W1', 'W2'], dataset_reference_work_ids={'W9'}
    )
    assert cls == 'fresh'


def test_classify_citing_work_fresh_when_dataset_has_no_references():
    cls = classify_citing_work(
        citing_referenced_work_ids=['W1'], dataset_reference_work_ids=set()
    )
    assert cls == 'fresh'


def test_citing_person_key_prefers_orcid():
    key, key_type = citing_person_key(
        {'name': 'Jane Doe', 'orcid': '0000-0001-2345-6789'}
    )
    assert (key, key_type) == ('0000-0001-2345-6789', 'orcid')


def test_citing_person_key_falls_back_to_normalised_name():
    key, key_type = citing_person_key({'name': '  Jane DOE  ', 'orcid': None})
    assert (key, key_type) == ('jane doe', 'name')


def test_citing_person_key_empty_when_nothing_identifying():
    key, key_type = citing_person_key({'name': None, 'orcid': None})
    assert (key, key_type) == ('', 'name')
