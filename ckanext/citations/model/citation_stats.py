"""Per-dataset citation/impact summary - the cached numbers shown on package/read.html.

Kept in its own table rather than package_extra so refreshing it never touches
package_revision or triggers a Solr reindex (see README "Why dedicated tables").
"""

from ckan.model import Package, meta
from ckan.model.domain_object import DomainObject
from sqlalchemy import Column, ForeignKey, Table, types
from sqlalchemy.orm import backref, relationship

citation_stats_table = Table(
    'fair_citation_stats',
    meta.metadata,
    Column(
        'package_id',
        types.UnicodeText,
        ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    ),
    # Resolved OpenAlex work id for this dataset's own DOI (e.g. "W1234567890"),
    # cached so refresh runs don't re-resolve the DOI -> work id every time.
    Column('openalex_work_id', types.UnicodeText, nullable=True),
    Column('citation_count_current', types.Integer, nullable=False, default=0),
    Column('citation_count_max', types.Integer, nullable=False, default=0),
    # Wu/Wang/Evans (2019) disruption index, range [-1, 1]. Null until the
    # dataset has at least one citing work (nothing to compute yet).
    Column('disruption_index', types.Float, nullable=True),
    Column('n_fresh', types.Integer, nullable=True),
    Column('n_building', types.Integer, nullable=True),
    Column('n_reference_only', types.Integer, nullable=True),
    Column('last_checked', types.DateTime, nullable=True),
)


class CitationStats(DomainObject):
    """Cached citation/disruption-index summary for one dataset."""


meta.registry.map_imperatively(
    CitationStats,
    citation_stats_table,
    properties={
        'dataset': relationship(
            Package,
            backref=backref(
                'citation_stats', uselist=False, cascade='all, delete-orphan'
            ),
            primaryjoin=citation_stats_table.c.package_id.__eq__(Package.id),
        )
    },
)
