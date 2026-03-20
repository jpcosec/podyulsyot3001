# Post-Key Validation and StepStone Autoapply Plan

## Current Status

- Listing crawl works for both sources with at least two pages.
- TU Berlin listing support has been restored in the new scraping subsystem.
- Translation length failures were fixed with chunked translation.
- Full prep-match runs are currently blocked by invalid Gemini API credentials.

## What To Execute After API Key Is Fixed

Use the same sample jobs already validated from listing page 1 and page 2.

### 1) Re-run listing smoke checks (2 pages each)

```bash
python -m src.cli.run_scrape_probe \
  --source tu_berlin \
  --url "https://www.jobs.tu-berlin.de/en/job-postings" \
  --mode listing \
  --max-pages 2 \
  --run-id tu-post-key

python -m src.cli.run_scrape_probe \
  --source stepstone \
  --url "https://www.stepstone.de/jobs/data-science?whatType=skillAutosuggest&action=facet_selected%3bage%3bage_1&ag=age_1&searchOrigin=Resultlist_top-search" \
  --mode listing \
  --max-pages 2 \
  --run-id ss-post-key
```

### 2) Full runs for 2 jobs from each listing page

#### TU Berlin samples

Page 1:

- `202362` -> `https://www.jobs.tu-berlin.de/en/job-postings/202362`
- `200522` -> `https://www.jobs.tu-berlin.de/en/job-postings/200522`

Page 2:

- `202645` -> `https://www.jobs.tu-berlin.de/en/job-postings/202645`
- `202644` -> `https://www.jobs.tu-berlin.de/en/job-postings/202644`

#### StepStone samples

Page 1:

- `13722751` -> `https://www.stepstone.de/stellenangebote--Data-Science-Trainee-w-m-d-Guetersloh-Bertelsmann-SE-Co-KGaA--13722751-inline.html`
- `13786215` -> `https://www.stepstone.de/stellenangebote--Teamlead-Data-Science-KI-all-genders-Koeln-Hamburg-Berlin-Muenchen-Karlsruhe-scieneers-GmbH--13786215-inline.html`

Page 2:

- `13798214` -> `https://www.stepstone.de/stellenangebote--Senior-Manager-Head-of-AI-Region-Sued-all-genders-Augsburg-Frankfurt-Karlsruhe-Koblenz-Koeln-Muenchen-Nuernberg-Stuttgart-Ulm-Walldorf-adesso-SE--13798214-inline.html`
- `13798713` -> `https://www.stepstone.de/stellenangebote--Praktikantin-fuer-Digitalisierungsumfaenge-im-Bereich-Konzeptqualitaet-und-Kundenerkenntnisse-Sindelfingen-Mercedes-Benz-AG--13798713-inline.html`

Each run command template:

```bash
python -m src.cli.run_prep_match \
  --source <source> \
  --job-id <job_id> \
  --source-url <detail_url> \
  --profile-evidence data/reference_data/profile/base_profile/profile_base_data.json \
  --run-id <tag>
```

### 3) Selection quality check focus

For each of the 8 jobs, inspect:

- `nodes/extract_understand/approved/state.json`
- `nodes/match/proposed/state.json`
- `nodes/match/review/decision.md`

Check whether requirement extraction and evidence matching quality differ by listing page.

## StepStone Autoapply Track

Use `src/cli/run_stepstone_autoapply.py` (added in this change) with safe defaults.

### Dry-run (default recommended)

```bash
python -m src.cli.run_stepstone_autoapply \
  --job-id 13722751 \
  --source-url "https://www.stepstone.de/stellenangebote--Data-Science-Trainee-w-m-d-Guetersloh-Bertelsmann-SE-Co-KGaA--13722751-inline.html"
```

### Attempt mode

```bash
python -m src.cli.run_stepstone_autoapply \
  --job-id 13722751 \
  --source-url "https://www.stepstone.de/stellenangebote--Data-Science-Trainee-w-m-d-Guetersloh-Bertelsmann-SE-Co-KGaA--13722751-inline.html" \
  --apply
```

Attempt mode intentionally fail-stops on login/captcha/manual-only states and records evidence artifacts.
