"""Cached S-index per ORCID - derived from COUNT(DISTINCT citing_person_key)
in fair_citing_researchers, refreshed by the CLI rather than computed on
every page view.
"""

from ckan.model import meta
from ckan.model.domain_object import DomainObject
from sqlalchemy import Column, Table, types

author_sindex_table = Table(
    'fair_author_sindex',
    meta.metadata,
    Column('orcid', types.UnicodeText, primary_key=True),
    Column('author_name', types.UnicodeText, nullable=True),
    Column('s_index_current', types.Integer, nullable=False, default=0),
    # High-water mark: a citing researcher's own identity can be deduplicated
    # differently by OpenAlex between two refresh runs (ORCID merges, name
    # disambiguation changes), which could otherwise cause the count to drop
    # even though nothing the author did changed. Never shown decreasing.
    Column('s_index_max', types.Integer, nullable=False, default=0),
    Column('dataset_count', types.Integer, nullable=False, default=0),
    Column('last_checked', types.DateTime, nullable=True),
)


class AuthorSIndex(DomainObject):
    """Cached S-index for one ORCID."""


meta.registry.map_imperatively(AuthorSIndex, author_sindex_table)
