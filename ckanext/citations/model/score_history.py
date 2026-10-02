"""Lightweight periodic snapshot of a dataset's citation count and disruption
index, so a future trend chart doesn't need to be designed into the schema
retroactively. Intentionally dataset-scoped only for v1 (no per-author
snapshot yet).
"""

from ckan.model import meta
from ckan.model.domain_object import DomainObject
from sqlalchemy import Column, ForeignKey, Table, types

score_history_table = Table(
    'fair_score_history',
    meta.metadata,
    Column('id', types.UnicodeText, primary_key=True),
    Column(
        'package_id',
        types.UnicodeText,
        ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False,
    ),
    Column('citation_count', types.Integer, nullable=False),
    Column('disruption_index', types.Float, nullable=True),
    Column('recorded_at', types.DateTime, nullable=False),
)


class ScoreHistory(DomainObject):
    """One periodic snapshot of a dataset's citation/disruption numbers."""


meta.registry.map_imperatively(ScoreHistory, score_history_table)
