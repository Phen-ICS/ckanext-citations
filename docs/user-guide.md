# User guide: the FAIR & Impact panel

Written for: researchers and curators who view or edit a FAIR3R dataset.

This guide explains the figures shown in the **FAIR & Impact** panel, at the bottom
of a dataset page, and how to read them.

## When the panel appears

The panel is shown on every public, active dataset. Citation tracking also needs a
**published DOI**. Without one, the panel says "Not checked yet": citations are not
tracked.

## Completeness

A coloured bar shows how complete the dataset's metadata is.

| Colour | Score |
|---|---|
| Red | below 50 % |
| Orange | 50 % to 79 % |
| Green | 80 % or more |

The score is a weighted share of the fields that apply to the dataset:

- **required** fields count twice, the other fields count once;
- the CKAN basics (title, description, tags, licence) count too;
- a field hidden by another answer (for example "transgene origin" when the
  "cross-species" box is not ticked) is not counted.

An unticked checkbox is not a missing field: not ticking it is a valid answer.

The "Missing fields" list gives, section by section, what is still to be filled.
Required fields are marked with an asterisk (*).

## Citations

The **citations** number is the count of works that cite the dataset's DOI, as
reported by OpenAlex. While OpenAlex does not yet know the DOI, the number comes
from DataCite Event Data.

The **Citing works** table lists the citing works, with title, authors, year,
venue and a DOI link.

## Disruption index

It ranges from **-1** to **+1**, following Wu, Wang & Evans (2019):

- close to **+1**: the works citing the dataset tend to replace it;
- close to **-1**: they build on the same references as the dataset.

It is computed from the dataset's references (its "References" or "Cites" related
identifiers in the metadata) and from the works citing those references.

**Limit to know**: to stay fast, the calculation uses a limited number of references
and a limited number of citing works per reference. When the references are very
widely cited, the index stays close to 0. Use it to compare datasets with each
other, not as an absolute value.

Without citations, the index is not computed ("not enough data yet").

## S-index

An author's S-index is the number of **distinct researchers** who wrote at least one
work citing one of that author's FAIR3R datasets. Researchers are identified by
their ORCID, or by their name when they have no ORCID.

- The score is **cumulative**: a researcher is never removed, even if their citation
  disappears later.
- When a dataset has several co-authors with an ORCID, the panel shows the highest
  S-index, and the per-co-author detail can be expanded.

The S-index measures how far the network of reached researchers extends, not the
quality of the citations.

## When the figures change

Citations and indices are recalculated once a week, on Sunday at night. A dataset is
recalculated only if it has not been checked for 7 days. The date of the last check
is shown next to the citations number.
