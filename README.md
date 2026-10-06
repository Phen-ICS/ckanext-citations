![CKAN](https://img.shields.io/badge/CKAN-2.12.0-orange)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)

# ckanext-citations

Citation tracking (cited-by, via OpenAlex with a DataCite Event Data
fallback), a per-dataset disruption index, and a per-researcher S-index
("how many unique researchers has your data enabled" - see
[s-index.science](https://s-index.science/)), displayed on the dataset
page.

## v1 scope

This first iteration deliberately does **not** implement the 17
FAIRsFAIR/F-UJI metrics, a merged "FAIR score", or the metadata-enrichment
assistant described in the original design note. It covers only the
citation/impact-tracking half:

- Citation count (cited-by) per dataset.
- [Disruption index](https://doi.org/10.1038/s41586-019-0941-9) (Wu, Wang &
  Evans, 2019): `DI = (N_F - N_B) / (N_F + N_B + N_R)`.
- S-index per ORCID: count of distinct researchers (deduplicated by ORCID,
  falling back to normalised name) who authored a work citing any of that
  researcher's FAIR3R datasets.
- Display on the dataset page (citation count, disruption index, S-index
  with a co-author breakdown, a citing-works table).

## Why dedicated tables, not `package_extra`

Citations and scores are refreshed by a periodic batch job, not by the user
editing the dataset. Writing them through `package_update`/`package_extra`
would create a `package_revision` row and trigger a full Solr reindex for
every dataset on every refresh run - pure overhead for data nobody searches
on. Instead this plugin owns five Postgres tables of its own
(`fair_citation_stats`, `fair_citing_works`, `fair_citing_researchers`,
`fair_author_sindex`, `fair_score_history`), created via the same
Alembic-based migration mechanism as `ckanext-doi`
(`ckan db upgrade -p citations`).

`fair_citing_researchers` exists only to make the S-index's "unique
researchers" dedup correct across an author's several datasets: it's one
row per (FAIR3R author ORCID, citing-researcher identity) pair, and
`fair_author_sindex.s_index_current` is the cached `COUNT(DISTINCT ...)`
over it. Both the citation count and the S-index are also tracked as
high-water marks (`*_max`) so a researcher's score never visibly regresses
just because an external API temporarily deduplicates differently between
two refresh runs.

## The disruption index needs a reference list the dataset usually doesn't have

The Wu/Wang/Evans formula needs to know what the focal work's own
references are, to tell "citing works that also build on the same sources"
(`N_B`) apart from "citing works that only cite the focal work" (`N_F`).
OpenAlex rarely has a populated reference list for a dataset-type Work,
which would make `N_B`/`N_R` collapse to 0 and the index trivially tend to
`+1.0` for almost every dataset with any citations at all.

To get a meaningful signal, the reference set is enriched with the
dataset's own DataCite `relatedIdentifiers` whose `relationType` is
`References` or `Cites` (already supported by the FDF schema via
`ckanext-doi`) - each such DOI is resolved to an OpenAlex work id and added
to the focal work's reference set before classifying citing works.

## Config

```ini
# Contact email sent as OpenAlex's "polite pool" mailto param (better rate
# limits, not auth). Optional but recommended.
ckanext.citations.contact_email = your-team@example.org

# Pause between outbound API calls during a refresh, in seconds.
ckanext.citations.request_pause_seconds = 0.1
```

## Bounding the disruption index

The reference set and the citers of each reference are capped, so a refresh
stays cheap even for a work with very popular references:

```ini
# At most this many references are used for the disruption index.
ckanext.citations.max_references = 10

# For each reference, only this many citing works are read.
ckanext.citations.max_reference_citers = 200
```

With these caps, the "reference only" count is an approximation, and the
disruption index is diluted by it. Read it as a relative signal.

## Running a refresh

```bash
ckan citations refresh --min-age-days 7
```

Idempotent and safe to run repeatedly: only datasets whose
`fair_citation_stats.last_checked` is older than `--min-age-days` (or
`NULL`, i.e. never checked) are touched. Intended to run from a weekly cron
job, same pattern as `fair3r update-schema`.

## Tests

Two `test.ini` files, same convention as the other FAIR3R extensions:

- `test.ini` at the repo root: Docker DEV (`/srv/app/src/ckan/test-core.ini`).
- `ckanext/citations/tests/test.ini`: shipped with the package, used by
  `deploy/ckanext_test.py` on integration/validation (`/usr/lib/ckan/default/...`).

```shell
docker exec -u ckan -it ckan-app pytest --ckan-ini=/plugins/ckanext-citations/test.ini /plugins/ckanext-citations/ckanext/citations/tests
```
