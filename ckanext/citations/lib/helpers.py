"""Template helper backing the dataset-page citations panel. Reads only
from this plugin's own tables - never touches Solr or package_extra."""

from ckan.model import Session

from ckanext.citations.lib.package_extras import get_creator_orcids
from ckanext.citations.model import AuthorSIndex, CitationStats, CitingWork


def citations_get_stats(package_id, package_dict=None):
    """Everything the citations_panel.html snippet needs for one dataset.
    When the dataset has never been checked, 'checked' is False and the
    numbers are empty, so the panel can still say so."""
    stats = Session.get(CitationStats, package_id)
    if stats is None:
        return {
            'checked': False,
            'citation_count': None,
            'disruption_index': None,
            'last_checked': None,
            'coauthors': [],
            'top_s_index': None,
            'citing_works': [],
        }

    citing_works = (
        Session.query(CitingWork)
        .filter(CitingWork.package_id == package_id)
        .order_by(CitingWork.year.desc().nullslast())
        .all()
    )

    coauthors = []
    if package_dict is not None:
        for orcid, name in get_creator_orcids(package_dict):
            sindex = Session.get(AuthorSIndex, orcid)
            coauthors.append(
                {
                    'orcid': orcid,
                    'name': name,
                    's_index': sindex.s_index_current if sindex else 0,
                }
            )
    coauthors.sort(key=lambda a: a['s_index'], reverse=True)

    return {
        'checked': True,
        'citation_count': stats.citation_count_current,
        'disruption_index': stats.disruption_index,
        'last_checked': stats.last_checked,
        'coauthors': coauthors,
        'top_s_index': coauthors[0]['s_index'] if coauthors else None,
        'citing_works': [
            {
                'title': cw.title,
                'authors': cw.authors,
                'year': cw.year,
                'venue': cw.venue,
                'doi': cw.citing_doi,
            }
            for cw in citing_works
        ],
    }


def citations_completeness(package_dict):
    """FAIR3R completeness for the panel, or None when ckanext-fair3r isn't installed."""
    try:
        from ckanext.fair3r.lib.fdf.completeness import completeness_for_package
    except ImportError:
        return None
    return completeness_for_package(package_dict)
