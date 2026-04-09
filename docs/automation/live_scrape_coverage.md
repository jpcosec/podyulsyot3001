# Live Scrape Coverage Notes

This document records the current live scrape coverage envelope observed from
real portal runs.

It is not a guarantee that every page variant is stable. It is the current
evidence baseline used to scope follow-up issues.

## StepStone

Validation sample run:

```bash
AUTOMATION_EXTRACTION_FALLBACKS=browseros python -m src.automation.main scrape --source stepstone --limit 3
```

Observed job ids:

- `13818645`
- `13867304`
- `13495192`

Observed outcomes:

- all 3 postings ingested successfully
- `company_name` remained correct across all 3 samples
- routing outcomes covered both `onsite` and `direct_url`

Observed heuristic-sensitive pattern:

- multi-location/hero metadata pages can still misclassify `location`
  - `data/jobs/stepstone/13867304/nodes/ingest/proposed/state.json`
  - `data/jobs/stepstone/13495192/nodes/ingest/proposed/state.json`
  - current extracted `location` = `Feste Anstellung`

Current confidence reading:

- StepStone company extraction is materially improved
- StepStone routing extraction is usable across the sampled variants
- StepStone location normalization is still not broad enough for some hero layouts

Follow-up:

- keep this coverage note as evidence
- track the remaining defect in a dedicated issue instead of treating coverage as unresolved forever
