"""Orchestrates one dataset's citation refresh: resolve its DOI on OpenAlex
(falling back to DataCite Event Data for a bare count if OpenAlex doesn't
know it yet), classify citing works for the disruption index, and feed the
S-index detail table. Pure DB writes live here; the formulas themselves are
in scoring.py and are unit-testable without a DB or network.
"""

import logging
import time
import uuid
from datetime import datetime, timezone

from ckan.model import Session
from ckan.plugins import toolkit

from ckanext.citations.lib import datacite_events_client, openalex_client
from ckanext.citations.lib.package_extras import (
    get_creator_orcids,
    get_published_doi,
    get_reference_dois,
)
from ckanext.citations.lib.scoring import (
    citing_person_key,
    classify_citing_work,
    disruption_index,
)
from ckanext.citations.model import (
    AuthorSIndex,
    CitationStats,
    CitingResearcher,
    CitingWork,
    ScoreHistory,
)

log = logging.getLogger(__name__)


def _contact_email():
    return toolkit.config.get('ckanext.citations.contact_email') or None


def _pause_seconds():
    try:
        return float(
            toolkit.config.get('ckanext.citations.request_pause_seconds', '0.1')
        )
    except (TypeError, ValueError):
        return 0.1


def refresh_dataset(package_id):
    """Refresh one dataset's citation/disruption numbers and S-index
    contribution. Safe to call repeatedly (idempotent upserts throughout)."""
    pkg = toolkit.get_action('package_show')({'ignore_auth': True}, {'id': package_id})

    doi = get_published_doi(pkg)
    if not doi:
        log.debug('Dataset %s has no published DOI yet, skipping', package_id)
        return

    contact_email = _contact_email()
    pause = _pause_seconds()

    stats = Session.get(CitationStats, package_id)
    if stats is None:
        # Column(default=0) only applies at flush/insert time, not on
        # construction - set these explicitly so the max()s below never see
        # None on a brand-new row.
        stats = CitationStats(
            package_id=package_id, citation_count_current=0, citation_count_max=0
        )
        Session.add(stats)

    work_id = stats.openalex_work_id or openalex_client.resolve_doi_to_work_id(
        doi, contact_email
    )

    if not work_id:
        _refresh_via_datacite_fallback(stats, doi)
        Session.commit()
        return

    stats.openalex_work_id = work_id

    focal = openalex_client.get_work(work_id, contact_email)
    reference_work_ids = set((focal or {}).get('referenced_work_ids') or [])

    for ref_doi in get_reference_dois(pkg):
        ref_work_id = openalex_client.resolve_doi_to_work_id(ref_doi, contact_email)
        if ref_work_id:
            reference_work_ids.add(ref_work_id)
        time.sleep(pause)

    citing_works = list(
        openalex_client.iter_citing_works(work_id, contact_email, pause_seconds=pause)
    )

    n_fresh = 0
    n_building = 0
    cited_focal_ids = set()
    now = datetime.now(timezone.utc)

    for cw in citing_works:
        cls = classify_citing_work(cw['referenced_work_ids'], reference_work_ids)
        if cls == 'building':
            n_building += 1
        else:
            n_fresh += 1
        if cw['openalex_work_id']:
            cited_focal_ids.add(cw['openalex_work_id'])
        _upsert_citing_work(package_id, cw, cls, now)

    n_reference_only = 0
    if reference_work_ids:
        reference_only_ids = set()
        for ref_id in reference_work_ids:
            for w in openalex_client.iter_citing_works(
                ref_id, contact_email, pause_seconds=pause
            ):
                wid = w['openalex_work_id']
                if wid and wid not in cited_focal_ids:
                    reference_only_ids.add(wid)
        n_reference_only = len(reference_only_ids)

    stats.citation_count_current = len(citing_works)
    stats.citation_count_max = max(
        stats.citation_count_max, stats.citation_count_current
    )
    stats.disruption_index = disruption_index(n_fresh, n_building, n_reference_only)
    stats.n_fresh = n_fresh
    stats.n_building = n_building
    stats.n_reference_only = n_reference_only
    stats.last_checked = now

    _update_sindex_contributions(pkg, citing_works, now)

    Session.add(
        ScoreHistory(
            id=str(uuid.uuid4()),
            package_id=package_id,
            citation_count=stats.citation_count_current,
            disruption_index=stats.disruption_index,
            recorded_at=now,
        )
    )

    Session.commit()


def _refresh_via_datacite_fallback(stats, doi):
    """OpenAlex has no Work for this DOI yet - fall back to a bare citing-DOI
    count from DataCite Event Data. No author/reference data, so the
    disruption index and S-index stay untouched."""
    try:
        citing_dois = datacite_events_client.get_citing_dois(doi)
    except datacite_events_client.DataciteEventsError:
        log.exception('DataCite Event Data fallback failed for DOI %s', doi)
        return
    stats.citation_count_current = len(citing_dois)
    stats.citation_count_max = max(
        stats.citation_count_max, stats.citation_count_current
    )
    stats.last_checked = datetime.now(timezone.utc)


def _upsert_citing_work(package_id, cw, disruption_class, now):
    existing = (
        Session.query(CitingWork)
        .filter(
            CitingWork.package_id == package_id, CitingWork.citing_doi == cw.get('doi')
        )
        .first()
    )
    if existing:
        existing.title = cw.get('title')
        existing.authors = cw.get('authors')
        existing.year = cw.get('year')
        existing.venue = cw.get('venue')
        existing.disruption_class = disruption_class
        existing.openalex_work_id = cw.get('openalex_work_id')
        return
    Session.add(
        CitingWork(
            id=str(uuid.uuid4()),
            package_id=package_id,
            citing_doi=cw.get('doi'),
            openalex_work_id=cw.get('openalex_work_id'),
            title=cw.get('title'),
            authors=cw.get('authors'),
            year=cw.get('year'),
            venue=cw.get('venue'),
            source='openalex',
            disruption_class=disruption_class,
            discovered_at=now,
        )
    )


def _update_sindex_contributions(pkg, citing_works, now):
    """For every FAIR3R creator of this dataset who has an ORCID, record
    every uniquely-identified citing author - then refresh their cached
    S-index from the deduplicated detail table."""
    focal_authors = get_creator_orcids(pkg)
    if not focal_authors:
        return

    citing_people = []
    for cw in citing_works:
        for author in cw.get('authors') or []:
            key, key_type = citing_person_key(author)
            if key:
                citing_people.append((key, key_type, author.get('name')))

    for orcid, author_name in focal_authors:
        for key, key_type, display_name in citing_people:
            existing = (
                Session.query(CitingResearcher)
                .filter(
                    CitingResearcher.author_orcid == orcid,
                    CitingResearcher.citing_person_key == key,
                )
                .first()
            )
            if existing:
                continue
            Session.add(
                CitingResearcher(
                    id=str(uuid.uuid4()),
                    author_orcid=orcid,
                    citing_person_key=key,
                    citing_person_display_name=display_name,
                    citing_person_key_type=key_type,
                    package_id=pkg['id'],
                    discovered_at=now,
                )
            )

        _refresh_author_sindex(orcid, author_name, now)


def _refresh_author_sindex(orcid, author_name, now):
    Session.flush()
    count = (
        Session.query(CitingResearcher)
        .filter(CitingResearcher.author_orcid == orcid)
        .count()
    )
    record = Session.query(AuthorSIndex).filter(AuthorSIndex.orcid == orcid).first()
    if record is None:
        record = AuthorSIndex(orcid=orcid, dataset_count=0)
        Session.add(record)
    record.author_name = author_name or record.author_name
    record.s_index_current = count
    record.s_index_max = max(record.s_index_max or 0, count)
    record.last_checked = now
