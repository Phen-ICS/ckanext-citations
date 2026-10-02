"""Pure calculation functions - no network, no DB session. Kept separate from
refresh.py so the formulas can be unit-tested without mocking HTTP calls.
"""


def disruption_index(n_fresh, n_building, n_reference_only):
    """Wu, Wang & Evans (2019): DI = (N_F - N_B) / (N_F + N_B + N_R).

    Returns None when the denominator is 0 (nothing cites the dataset or its
    references yet) rather than raising - "no signal yet" is a normal state
    for a newly-registered dataset, not an error.
    """
    denominator = n_fresh + n_building + n_reference_only
    if denominator == 0:
        return None
    return (n_fresh - n_building) / denominator


def classify_citing_work(citing_referenced_work_ids, dataset_reference_work_ids):
    """'building' if the citing work also cites at least one of the
    dataset's own references, else 'fresh'."""
    if dataset_reference_work_ids and set(citing_referenced_work_ids) & set(
        dataset_reference_work_ids
    ):
        return 'building'
    return 'fresh'


def citing_person_key(author):
    """Dedup identity for one author dict ({"name": ..., "orcid": ...}):
    prefer ORCID, fall back to a normalised name. Returns (key, key_type).
    """
    orcid = (author.get('orcid') or '').strip()
    if orcid:
        return orcid, 'orcid'
    name = (author.get('name') or '').strip().lower()
    return name, 'name'
