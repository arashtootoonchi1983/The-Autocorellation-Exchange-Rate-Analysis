# Global Infrastructure Megaprojects Dataset

40 well-documented, real, public-infrastructure / megaprojects with **planned vs. actual** cost and schedule, plus a `budget_revision_history` field capturing the *time-vs-price* trajectory during execution.

File: `global_infrastructure_megaprojects_dataset.csv`

## Columns

| column | meaning |
|---|---|
| project_id | sequential ID (P001 … P040) |
| project_name | common project name |
| project_type | high-level category (Highway, Rail, Bridge, Dam/Hydro, Energy, Airport, Canal, Building, Water) |
| sub_type | finer classification (e.g. "Subsea rail tunnel", "Nuclear power plant") |
| country | host country (or countries) |
| region | geographical region |
| planned_start_year | year construction was approved/started per original plan |
| planned_end_year | originally announced completion year |
| planned_duration_years | planned_end_year − planned_start_year |
| planned_cost_local_currency | currency code of original budget |
| planned_cost_local_value_billion | original-currency budget in billions |
| planned_cost_year_basis | the price-base year of the original estimate |
| planned_cost_usd_billion_nominal | best-effort USD-billion equivalent at the planning year |
| actual_start_year | year actual construction began |
| actual_end_year | actual / projected completion year |
| actual_duration_years | actual_end_year − actual_start_year |
| actual_cost_local_currency | local currency of final reported cost |
| actual_cost_local_value_billion | final / latest reported cost in original currency, billions |
| actual_cost_usd_billion_nominal | final cost in USD billions (nominal at completion) |
| cost_overrun_percent | (actual − planned) / planned × 100, both in like-for-like local currency where possible |
| time_overrun_years | actual_end_year − planned_end_year (negative = early) |
| status | Completed / In progress |
| budget_revision_history | semicolon-separated `year:value` entries showing how the budget was revised through the project — this is the *time-vs-price record during execution* |
| primary_source | URL of primary public reference |

## Notes / caveats

- **Like-for-like comparison is hard.** Some original budgets are quoted in the price-base year (e.g. Channel Tunnel £2.6B in 1985 prices) and some final figures are nominal at completion. Where both are widely cited the local-currency overrun column uses the most commonly-quoted comparison (the same one used in Flyvbjerg / public-accounts reports).
- **In-progress projects** (California HSR, HS2, Hinkley Point C, Honolulu Rail, Stuttgart 21, MOSE, Site C, Brisbane CRR) carry the latest publicly disclosed forecast as of 2025; they will continue to drift.
- **Budget revisions are not exhaustive** — only the publicly milestone-marked revisions are listed. For a fully-resolved monthly/quarterly time-series of cost-at-completion you would need:
  - GAO Major Project Assessments (NASA / DOE / DoD) for U.S. federal projects
  - UK NAO + Public Accounts Committee reports (Crossrail, HS2, Hinkley)
  - MTA Capital Program Oversight Committee minutes (East Side Access, Second Avenue Subway)
  - Caltrans / WSDOT / MassDOT change-order logs
  - World Bank Implementation Completion and Results Reports (ICRs)
- **Currency conversions** use the FX rate of the budget-/completion-year (rough, not inflation-corrected). For autocorrelation/exchange-rate work, use the local-currency columns and convert with your own FX series.

## Project type breakdown

- Rail (12): Channel Tunnel, Crossrail, CHSR, HS2, HS1, Gotthard, Stuttgart 21, East Side Access, 2nd Av Subway, Honolulu Rail, Edinburgh Trams, Brisbane CRR, Riyadh Metro
- Energy / Nuclear / Hydro (6): Vogtle, Hinkley C, Olkiluoto 3, Flamanville 3, Three Gorges, Itaipu, Hoover, Site C
- Airport (5): BER, Heathrow T5, Denver, Hong Kong, Istanbul, Beijing Daxing
- Bridge (4): HK-Zhuhai-Macau, Øresund, Great Belt, Tappan Zee, Hoover Bypass
- Highway / Tunnel (2): Big Dig, SR 99 Seattle
- Canal (2): Panama, New Suez
- Building (2): Sydney Opera House, Empire State Building, Burj Khalifa
- Water / coastal (1): MOSE Venice
- Dam (covered above)

## How to use this for autocorrelation / exchange-rate work

The `budget_revision_history` field is the seed for a panel time-series of `cost_t` per project. Combining with monthly FX rates (host-country currency vs. USD or vs. a basket) lets you test whether revisions correlate with FX shocks, commodity-price swings, or domestic CPI / construction-cost-index moves — which appears to be the focus of this repo (`iran_construction_materials_*` and `iran_macroeconomic_*` files).

## License

Public-domain compilation of publicly-available facts. Original sources retain their own licensing (mostly Wikipedia CC-BY-SA, government reports public-domain).
