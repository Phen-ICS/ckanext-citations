"""One row per (dataset, work that cites it) - backs the "citing articles" table
on the dataset page, and carries the fresh/building split used for the
disruption index.
"""

from ckan.model import Package, meta
from ckan.model.domain_object import DomainObject
from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, types
from sqlalchemy.orm import relationship

citing_work_table = Table(
    'fair_citing_works',
    meta.metadata,
    Column('id', types.UnicodeText, primary_key=True),
    Column(
        'package_id',
        types.UnicodeText,
        ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('citing_doi', types.UnicodeText, nullable=True),
    Column('openalex_work_id', types.UnicodeText, nullable=True),
    Column('title', types.UnicodeText, nullable=True),
    # [{"name": ..., "orcid": ...}, ...] - kept denormalised (JSON), this is a
    # display cache, not something queried by author.
    Column('authors', types.JSON, nullable=True),
    Column('year', types.Integer, nullable=True),
    Column('venue', types.UnicodeText, nullable=True),
    Column('source', types.UnicodeText, nullable=False, default='openalex'),
    # Disruption-index classification of this citing work relative to the
    # dataset's own reference set: 'fresh' (N_F), 'building' (N_B), or
    # 'reference_only' is tracked separately (those works never cite the
    # dataset itself, so they have no row here at all).
    Column('disruption_class', types.UnicodeText, nullable=True),
    Column('discovered_at', types.DateTime, nullable=False),
    UniqueConstraint(
        'package_id', 'citing_doi', name='fair_citing_works_package_doi_key'
    ),
)


class CitingWork(DomainObject):
    """A single work that cites a FAIR3R dataset."""


meta.registry.map_imperatively(
    CitingWork,
    citing_work_table,
    properties={
        'dataset': relationship(
            Package,
            primaryjoin=citing_work_table.c.package_id.__eq__(Package.id),
        )
    },
)
