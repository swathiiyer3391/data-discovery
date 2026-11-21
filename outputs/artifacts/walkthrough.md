# End-to-End Discovery Walkthrough

This walkthrough traces four concrete artifacts from my UC1 and UC2 discovery runs, citing the exact files in this repository.

---

## 1. One Deterministic Rule I Wrote (`discovery_agent/risk_rules.py`)

In `discovery_agent/risk_rules.py` (Gap G4), I implemented three deterministic feasibility rules executed between profiling and risk assessment:
1. **Window coverage and staleness (`check_window_coverage_and_staleness`):** Compares each source's `temporal.start`, `temporal.end`, and `temporal.open_ended` against the required windows in `use_cases/<ID>_*.json` and computes data age against `use_case["as_of"]` (`2026-11-20` for UC1, `2026-04-01` for UC2) using `config/settings.json` (`stale_after_days: 365`). It raises `COV-NO-WINDOW-OVERLAP` (blocker) when zero days overlap, `COV-PARTIAL-WINDOW` (major) when a source covers only part of a required window (for example, `link.europa_sdg_11_52_099aa6` ending in `2023` while UC1's production window spans `2024-01-01` to `2025-12-31`), and `FRS-STALE` (major) when data age exceeds 365 days (for example, `link.uci_360` ending `2005-04-04`, ~21.5 years before `as_of`).
2. **Grain mismatch (`check_grain_mismatch`):** Ranks temporal grains (`minute` < `15min` < `30min` < `hourly` < `daily` < `weekly` < `monthly` < `quarterly` < `annual`) and raises `GRN-TOO-COARSE` (blocker) when a source's `temporal.grain` is coarser than every need it targets (such as annual data mapped to an hourly need).
3. **Metadata-versus-documentation contradiction (`check_metadata_contradiction`):** Cross-checks structured `declared_metadata` flags (such as `"has_missing_values": "no"` or `"no missing values"`) against `documentation_excerpts`, `quality_notes`, and `sample_findings` for evidence of missing values, sentinel encodings (`-200`), or outages, raising `DQ-METADATA-CONTRADICTION` (major) on `link.uci_360` and `internal.sales.daily_by_product`.

---

## 2. One Claim in `signoff.json` Traced to Its Record Field

In `outputs/UC1/signoff.json`, the `traced_conclusion` cites:
- **`source_id`:** `internal.airq.station_readings`
- **`record_field`:** `temporal.start`
- **Record evidence (`outputs/UC1/records/internal.airq.station_readings.json`):** `temporal.start` is `"2023-01-01"` (`temporal.open_ended: true`, `temporal.grain: "hourly"`). Because Valdena's internal monitoring network only began recording on `2023-01-01`, it covers UC1's production window (`2024-01-01` to `2025-12-31`) but has zero overlap with the prototype window (`2004-03-10` to `2005-04-04`).
- **Why this drives the project decision (`could_change_if`):** That gap is the reason UC1 relies on `link.uci_360` as a historical prototype proxy for N1 while requiring access approval from Giulia Rossi (Environment Monitoring Unit) and handling the `2024-06-30` Station VR-03 shutdown for production. If `internal.airq.station_readings` actually extended back to 2004 (or if Environment Monitoring denied production access), the prototype proxy requirement or production feasibility verdict would change immediately.

---

## 3. One Rejected Source and Why

- **Source:** `https://catalog.data.gov/dataset/open-air-chicago-hour-aggregations` (`link.data_open_air_chicago_hour_aggre_d4970b` in `outputs/UC1/links.json` and `outputs/UC1/discovery_results.json`)
- **Gate & Guardrail Handling:** In `outputs/UC1/gate_decisions.json`, I intentionally set `"decision": "accept"` at the candidate gate while keeping `catalog.data.gov` out of `config/allowlist.json` (documented under G6 in `outputs/artifacts/decisions.md`). During profiling (`outputs/UC1/trace.jsonl`), `inspect_dataset_link` enforced the exact-host allowlist and returned `DOMAIN_NOT_ALLOWLISTED`, recording an auditable guardrail refusal without fetching external bytes.
- **Why it is `not_feasible`:** Three independent blockers prevent use: (1) `ACC-UNREACHABLE` because `catalog.data.gov` is not an approved host, (2) `LIC-UNKNOWN` because no licence could be verified through the allowlist, and (3) `COV-GEO-MISMATCH` because the dataset covers Chicago, Illinois (USA) rather than Valdena in northern Italy.

---

## 4. One Memo Conclusion Verified Against Records and Traces

- **Conclusion (`outputs/UC2/feasibility_memo.md`, Sections 1–3):** UC2 is **`feasible_with_conditions`** overall, with `internal.sales.daily_by_product` rated **`feasible_with_conditions`** for N1 (`Daily ice-cream sales by product`).
- **Verification against `outputs/UC2/records/internal.sales.daily_by_product.json` and `outputs/UC2/rule_flags.json`:**
  1. `access.auth_required` is `true` (`classification: "confidential"`, steward Marco Bianchi in Retail Operations), triggering `ACC-RESTRICTED`.
  2. `temporal.start` is `"2022-01-01"` (`grain: "daily"`), covering both `history` (`2023-06-01` to `2025-05-31`) and `recent` (`2025-06-01` to `2026-03-31`), **except** that `documentation_excerpts` (wiki `till_migration_2024`) document a 34-day outage from `2024-02-05` to `2024-03-10` that must be treated as missing data rather than zero sales (`COV-PARTIAL-WINDOW` and `DQ-METADATA-CONTRADICTION`).
  3. On `2024-04-01`, product codes ending in `L` were replaced without a lookup table (`DQ-SEMANTIC-ENCODING`), requiring reconstruction of a partial mapping from distinct `product_code` values before and after `2024-04-01` for N2.
  Because every condition is operationally actionable by the data team and Retail Operations, `proceed_with_conditions` in `outputs/UC2/signoff.json` is fully supported by the underlying record provenance.
