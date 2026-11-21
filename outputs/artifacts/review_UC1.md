# Memo Review — UC1 (Air Quality, Traffic, Weather & Clinic Surveillance)

- **Reviewer:** Swathi Iyer
- **Overall Agent Verdict:** `feasible_with_conditions`
- **Reviewer Gate Decision:** `proceed_with_conditions`

## 1. Where I Agree with the Agent
- **Overall feasibility (`feasible_with_conditions`):** All three MUST needs (N1 air quality, N2 traffic, N3 weather) have viable paths across prototype and production windows, while N5 (patient-level records) is a `could` need properly excluded by DPO policy.
- **Internal sources & hidden traps caught:** The agent accurately surfaced the catalog-vs-wiki conflict on `internal.airq.station_readings` (Station VR-03 decommissioned `2024-06-30`), the `2024-03-18` counter replacement direction-encoding break in `internal.traffic.hourly_counts`, the missing spatial join keys across air/traffic/clinic tables, and the DPO prohibition on `internal.clinic.patient_visits`.
- **External register sources:** Agree with `feasible` for `api.nager_public_holidays`, `feasible_with_conditions` for `api.open_meteo_archive` (requires northern Italy coordinates and CC BY 4.0 attribution/upstream licence check), and `not_feasible` for `vendor.atmosdata_pro` (contract AD-2021-114 expired `2025-12-31`, API key revoked).

## 2. Where I Overrule or Clarify the Agent
- **Minor date correction on `link.uci_360`:** Section 3 of `feasibility_memo.md` describes the UCI dataset as covering *"March 2004 – February 2005"*, whereas the actual profiled temporal range runs through `2005-04-04` (April 2005), covering the full prototype window. The `feasible_with_conditions` verdict and dismissal of `FRS-STALE` for prototype benchmark use remain valid.

## 3. Dataset Link Verdicts & Gate Decisions
1. **`https://archive.ics.uci.edu/dataset/360/air+quality` (`link.uci_360`)**
   - **Gate Decision:** `accept` (host `archive.ics.uci.edu` already allowlisted; matches prototype window `2004-03-10` to `2005-04-04` for N1/N3).
   - **Final Verdict:** `feasible_with_conditions` (prototype only; replace `-200` sentinel values with `NULL`, verify city context, and obtain legal sign-off on CC BY 4.0 vs. prose research-only restriction).
2. **`https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sdg_11_52?format=JSON&lang=EN&geo=IT` (`link.europa_sdg_11_52_099aa6`)**
   - **Gate Decision:** `accept` (after inspecting Eurostat terms and adding exact host `ec.europa.eu` to `config/allowlist.json` under G6).
   - **Final Verdict:** `feasible_with_conditions` (partially meets `could` need N6 for 2005–2023 national PM2.5 mortality context; requires CC BY 4.0 attribution and documentation of missing 2004/2024–2025 years and 2007 methodology break).
3. **`https://catalog.data.gov/dataset/open-air-chicago-hour-aggregations` (`link.data_open_air_chicago_hour_aggre_d4970b`)**
   - **Gate Decision:** `accept` at candidate gate specifically to test and record the guardrail refusal as an auditable finding without allowlisting `catalog.data.gov`.
   - **Final Verdict:** `not_feasible` (blocked by `ACC-UNREACHABLE`, `LIC-UNKNOWN`, and `COV-GEO-MISMATCH` — Chicago, USA vs. Valdena, Italy).
