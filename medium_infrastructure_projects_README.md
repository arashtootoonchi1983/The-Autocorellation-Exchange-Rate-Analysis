# Medium-Scale Infrastructure Projects Dataset

30 publicly-funded "large but not megaproject" projects ($15M – $2.5B) across diverse typologies, with **planned vs. actual** cost, schedule, and a `budget_revision_history` column capturing the cost-vs-time trajectory **during execution** (the cost-to-complete revisions disclosed at major milestones).

File: `medium_infrastructure_projects_dataset.csv` — companion to `global_infrastructure_megaprojects_dataset.csv`.

## Why a separate, mid-size dataset

The megaproject dataset is dominated by a few project types (rail, dams, nuclear). This file deliberately spreads the typology to:

- **Bus rapid transit** – 3 projects (Cleveland HealthLine, Eugene EmX Green Line, Eugene EmX West)
- **Modern streetcar** – 6 projects (Tucson, Cincinnati, Detroit, DC, Atlanta, Kansas City)
- **Light rail extensions** – 4 projects (Norfolk Tide, Phoenix Central Mesa, Charlotte LYNX BLE, LA Crenshaw, Boston GLX)
- **VA hospitals** – 4 projects (Aurora/Denver, Orlando, Las Vegas, New Orleans) – richest available cost-revision histories thanks to GAO oversight
- **Federal courthouses** – 3 projects (Los Angeles, San Diego, Salt Lake City)
- **Bridges (small/medium)** – 1 (Hoover Dam Bypass)
- **Highway** – 1 (Indiana I-69 Section 5 P3)
- **Water treatment** – 1 (Wichita NW WTF)
- **Public libraries / civic** – 3 (Winter Park, Santa Cruz, Maitland)
- **University research building** – 1 (UW Population Health)
- **Federal office** – 1 (Census Bureau Suitland)

## Columns (same shape as the megaproject CSV, with size_metric added)

| column | meaning |
|---|---|
| project_id | sequential ID (M001 … M030) |
| project_name | common project name |
| project_type | high-level category (Transit, Healthcare, Building, Bridge, Highway, Water) |
| sub_type | finer classification |
| country / region | geography |
| size_metric | descriptive size (miles, sq ft, beds, MGD, etc.) — useful for unit-cost normalisation |
| planned_start_year, planned_end_year, planned_duration_years | original baseline schedule |
| planned_cost_local_currency / planned_cost_local_value_million | original budget at the planned-cost-year-basis |
| actual_start_year, actual_end_year, actual_duration_years | as-built schedule |
| actual_cost_local_currency / actual_cost_local_value_million | final / latest reported cost |
| cost_overrun_percent | (actual − planned) / planned × 100 in like-for-like currency |
| time_overrun_years | actual_end_year − planned_end_year |
| status | Completed / In progress / Cancelled |
| budget_revision_history | semicolon-separated `year:value` entries — the *time-vs-price record during execution* |
| primary_source | URL of primary public reference (FTA, GAO, agency report, Wikipedia) |

## Where the mid-project revision data comes from

- **FTA Before-and-After Studies** for New Starts / Small Starts transit projects — multiple "prediction milestones" (entry into engineering, FFGA, opening) with reported costs at each. Particularly clean for Phoenix Central Mesa, Charlotte LYNX BLE, Eugene EmX, Norfolk Tide.
- **GAO oversight reports** for VA hospitals, federal courthouses, federal buildings — congressional testimony with cost revisions year-by-year.
- **Local agency capital-program reports** (MBTA Green Line Extension, LA Metro Crenshaw/K Line) — quarterly cost-to-complete updates.
- **State auditor reports** (Indiana I-69 Section 5 P3 default) — court filings disclose revision history.
- **City council meeting minutes / GMP amendments** for the smaller civic projects.

## Caveats

- `cost_overrun_percent` uses nominal local-currency comparison; not inflation-corrected.
- `budget_revision_history` lists only **publicly disclosed milestones**, not every internal revision. For continuous (monthly) cost data you would need to file a public-records request with the agency.
- Some "actual" figures for in-progress projects (Wichita WTF, Santa Cruz Library, Maitland Library) are the latest disclosed forecast and will continue to drift.
- Some projects (Eugene EmX Green Line, Phoenix Central Mesa, Kansas City Streetcar, UW Population Health, Charlotte LYNX BLE) are explicitly cited by FTA / GAO as **on-time / on-budget exemplars** — included intentionally so the dataset is not biased toward failures.

## Combined with the megaproject dataset

You now have:
- `global_infrastructure_megaprojects_dataset.csv` (40 rows, $1B – $130B)
- `medium_infrastructure_projects_dataset.csv` (30 rows, $15M – $2.5B)

= **70 documented projects** spanning four orders of magnitude of project size, suitable for autocorrelation / FX / cost-driver analysis.
