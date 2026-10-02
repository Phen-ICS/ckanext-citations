"""Detail table behind the S-index (s-index.science model: "how many unique
researchers has your data enabled").

A FAIR3R author's S-index is COUNT(DISTINCT citing_person_key) across every
one of their datasets - that dedup only works if we keep one row per
(author_orcid, citing_person_key) pair rather than a flat per-dataset count,
otherwise the same citing researcher would be counted once per dataset of
theirs they cite, inflating the score for authors with several datasets.
"""

from ckan.model import meta
from ckan.model.domain_object import DomainObject
from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, types

citing_researcher_table = Table(
    'fair_citing_researchers',
    meta.metadata,
    Column('id', types.UnicodeText, primary_key=True),
    # The FAIR3R dataset author whose S-index this row counts towards.
    Column('author_orcid', types.UnicodeText, nullable=False),
    # Dedup identity of the citing researcher: their ORCID when OpenAlex gives
    # one, otherwise a normalised "name" fallback key. Name-based keys are a
    # weaker identity (collisions possible) but better than not counting them.
    Column('citing_person_key', types.UnicodeText, nullable=False),
    Column('citing_person_display_name', types.UnicodeText, nullable=True),
    Column(
        'citing_person_key_type', types.UnicodeText, nullable=False
    ),  # 'orcid' | 'name'
    # Which dataset mediated the discovery (for traceability/debugging only;
    # not part of the dedup key, since the whole point is de-duplicating
    # across a researcher's several datasets).
    Column(
        'package_id',
        types.UnicodeText,
        ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('discovered_at', types.DateTime, nullable=False),
    UniqueConstraint(
        'author_orcid',
        'citing_person_key',
        name='fair_citing_researchers_orcid_person_key',
    ),
)


class CitingResearcher(DomainObject):
    """One (FAIR3R author, unique citing researcher) pair."""


meta.registry.map_imperatively(CitingResearcher, citing_researcher_table)
