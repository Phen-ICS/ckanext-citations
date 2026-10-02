"""Initialisation.

Revision ID: 8f3b2c1a9d4e
Revises:
Create Date: 2026-10-01 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

revision = '8f3b2c1a9d4e'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(name):
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    return name in insp.get_table_names()


def upgrade():
    if not _table_exists('fair_citation_stats'):
        op.create_table(
            'fair_citation_stats',
            sa.Column(
                'package_id',
                sa.UnicodeText,
                sa.ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
                primary_key=True,
            ),
            sa.Column('openalex_work_id', sa.UnicodeText, nullable=True),
            sa.Column(
                'citation_count_current', sa.Integer, nullable=False, server_default='0'
            ),
            sa.Column(
                'citation_count_max', sa.Integer, nullable=False, server_default='0'
            ),
            sa.Column('disruption_index', sa.Float, nullable=True),
            sa.Column('n_fresh', sa.Integer, nullable=True),
            sa.Column('n_building', sa.Integer, nullable=True),
            sa.Column('n_reference_only', sa.Integer, nullable=True),
            sa.Column('last_checked', sa.DateTime, nullable=True),
        )

    if not _table_exists('fair_citing_works'):
        op.create_table(
            'fair_citing_works',
            sa.Column('id', sa.UnicodeText, primary_key=True),
            sa.Column(
                'package_id',
                sa.UnicodeText,
                sa.ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('citing_doi', sa.UnicodeText, nullable=True),
            sa.Column('openalex_work_id', sa.UnicodeText, nullable=True),
            sa.Column('title', sa.UnicodeText, nullable=True),
            sa.Column('authors', sa.JSON, nullable=True),
            sa.Column('year', sa.Integer, nullable=True),
            sa.Column('venue', sa.UnicodeText, nullable=True),
            sa.Column(
                'source', sa.UnicodeText, nullable=False, server_default='openalex'
            ),
            sa.Column('disruption_class', sa.UnicodeText, nullable=True),
            sa.Column('discovered_at', sa.DateTime, nullable=False),
            sa.UniqueConstraint(
                'package_id', 'citing_doi', name='fair_citing_works_package_doi_key'
            ),
        )

    if not _table_exists('fair_citing_researchers'):
        op.create_table(
            'fair_citing_researchers',
            sa.Column('id', sa.UnicodeText, primary_key=True),
            sa.Column('author_orcid', sa.UnicodeText, nullable=False),
            sa.Column('citing_person_key', sa.UnicodeText, nullable=False),
            sa.Column('citing_person_display_name', sa.UnicodeText, nullable=True),
            sa.Column('citing_person_key_type', sa.UnicodeText, nullable=False),
            sa.Column(
                'package_id',
                sa.UnicodeText,
                sa.ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('discovered_at', sa.DateTime, nullable=False),
            sa.UniqueConstraint(
                'author_orcid',
                'citing_person_key',
                name='fair_citing_researchers_orcid_person_key',
            ),
        )

    if not _table_exists('fair_author_sindex'):
        op.create_table(
            'fair_author_sindex',
            sa.Column('orcid', sa.UnicodeText, primary_key=True),
            sa.Column('author_name', sa.UnicodeText, nullable=True),
            sa.Column(
                's_index_current', sa.Integer, nullable=False, server_default='0'
            ),
            sa.Column('s_index_max', sa.Integer, nullable=False, server_default='0'),
            sa.Column('dataset_count', sa.Integer, nullable=False, server_default='0'),
            sa.Column('last_checked', sa.DateTime, nullable=True),
        )

    if not _table_exists('fair_score_history'):
        op.create_table(
            'fair_score_history',
            sa.Column('id', sa.UnicodeText, primary_key=True),
            sa.Column(
                'package_id',
                sa.UnicodeText,
                sa.ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('citation_count', sa.Integer, nullable=False),
            sa.Column('disruption_index', sa.Float, nullable=True),
            sa.Column('recorded_at', sa.DateTime, nullable=False),
        )


def downgrade():
    op.drop_table('fair_score_history')
    op.drop_table('fair_author_sindex')
    op.drop_table('fair_citing_researchers')
    op.drop_table('fair_citing_works')
    op.drop_table('fair_citation_stats')
