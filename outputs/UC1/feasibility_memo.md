## 1. Executive summary

**Feasible with conditions — all three MUST needs can be met, but every one depends on access approvals not yet granted and data-quality issues that must be resolved before profiling.**

- N1 (hourly air pollutants) can be prototyped now on UCI Air Quality data (2004–2005); production requires the city's own station readings, but VR-03 stopped reporting on 2024-06-30, creating a six-month gap in the production window.
- N2 (hourly traffic) exists for the full production window but has a methodology break on 2024-03-18 (per-direction counts became combined direction), and counter locations are undocumented.
- N3 (hourly temperature/humidity) is met by Open-Meteo archive for both windows, subject to attribution and upstream-licence review.
- N4 (daily clinic visits, should) is approved by the DPO but its diagnosis criteria and district coding are undocumented.
- N5 (patient-level visits, could) is explicitly prohibited by the DPO and cannot be used.
- N6 (national PM2.5 deaths context, could) is partially met by Eurostat, ending in 2023.

## 2. Need coverage

| Need id | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations (NO₂, PM2.5) | must | met_with_conditions | link.uci_360 (prototype), internal.airq.station_readings (production) | UCI: ~17.5% missing NO₂, -200 sentinels, unnamed city. Internal: VR-03 gap from 2024-07-01, access not granted, no station locations for spatial join. |
| N2 | Hourly vehicle traffic near monitoring stations | must | met_with_conditions | internal.traffic.hourly_counts | Access not granted, counter break 2024-03-18 changes direction methodology, no counter-location metadata. |
| N3 | Hourly temperature and humidity | must | met_with_conditions | api.open_meteo_archive (both windows), link.uci_360 (prototype complement) | Coordinates must be set to northern Italy (not default Lisbon). Upstream licences need legal review. |
| N4 | Daily respiratory clinic visits, by district | should | met_with_conditions | internal.clinic.resp_visits_daily, api.nager_public_holidays | Access not granted. Diagnosis classification and district code system undocumented. No geography crosswalk to stations. |
| N5 | Patient-level clinic visit records | could | unmet | internal.clinic.patient_visits | DPO explicitly prohibits use for this analysis. Contains PII that cannot leave clinic systems. |
| N6 | National yearly context: deaths linked to PM2.5 | could | partially_met | link.europa_sdg_11_52_099aa6 | Data ends 2023 (no 2024–2025). 2006 missing. Methodology break pre/post 2007. National-level only. |

## 3. Source assessments

### api.nager_public_holidays — feasible
Public API returning Italian public holidays for 2024–2025 (13 holidays per year). MIT-licensed, no auth required. Supports N4 by identifying zero-visit days in clinic data. No red flags, no blockers.

### api.open_meteo_archive — feasible with conditions
ERA5/ERA5-Land reanalysis covering both windows hourly with temperature_2m and relative_humidity_2m. Probed successfully for March 2004 and Dec 2024/Jan 2025 at Milan-area coordinates (45.46, 9.19). **Conditions:** (1) Attribution text "Weather data by Open-Meteo.com" must accompany any displayed data. (2) Coordinates must be set to northern Italy — the register defaults to Lisbon. (3) Legal team must review mixed upstream licences (DWD CC-BY, ECMWF CC-BY, UK Met Office CC-BY-SA) before production use.

### internal.airq.station_readings — feasible with conditions
Hourly NO₂ and PM2.5 from Valdena's own stations (2023-01-01 onward, hourly refresh). Covers the production window for N1. Does **not** cover the prototype window. **Key flags:**
- **ACC-RESTRICTED (major):** Access request to Environment Monitoring Unit (Giulia Rossi) not yet granted.
- **GOV-CATALOG-WIKI-CONFLICT (major):** Catalog (exported 2026-10-14) shows no VR-03 closure. Wiki page 'station_network' (last_edited 2024-07-01) states "Station VR-03 (Via Roma) was switched off on 2024-06-30. Its readings stop there."
- **INT-NO-JOIN-KEY (major):** Schema has station_id but no coordinates. A separate station-location reference table is needed for spatial join with traffic counters.

**Conditions:** (1) Access must be granted. (2) VR-03 gap from 2024-07-01 must be documented and handled. (3) Station-location reference table must be sourced.

### internal.clinic.patient_visits — not feasible
Patient-level visit records (900K rows, 2019–present). **Flags:** ACC-RESTRICTED, GOV-PII (patient_key, age_band, postcode), GOV-CONSENT-GAP (wiki states "may not be used for this analysis"), GOV-PURPOSE-LIMITATION. The DPO explicitly prohibits use. No achievable condition can resolve. Superseded by internal.clinic.resp_visits_daily for the aggregated need.

### internal.clinic.resp_visits_daily — feasible with conditions
Daily respiratory visit counts by district (2022-01-01 onward, daily refresh). DPO-approved for this surveillance purpose. No PII. **Key flags:**
- **ACC-RESTRICTED (major):** Access request to Clinical Analytics (Chiara Conti) not yet granted.
- **DQ-UNDOCUMENTED-SCHEMA (major):** Diagnosis classification system (ICD-10 vs local coding) not documented. District code system is "string" with no enumerated list. District boundary stability for 2024–2025 unknown.
- **INT-NO-JOIN-KEY (major):** No crosswalk to link districts with station or counter locations.

**Conditions:** (1) Access must be granted. (2) Diagnosis criteria documented and verified. (3) District code system and boundary stability confirmed. (4) District-to-station-area crosswalk created.

### internal.traffic.hourly_counts — feasible with conditions
Hourly vehicle counts from road counters (2021-01-01 onward, hourly refresh). Covers the production window for N2. **Key flags:**
- **ACC-RESTRICTED (major):** Access request to Mobility Office (Luca Ferri) not yet granted.
- **DQ-METADATA-CONTRADICTION (major):** Catalog omits the counter replacement on 2024-03-18. Wiki page 'counter_replacement_2024' (last_edited 2024-04-02) documents the change.
- **DQ-SEMANTIC-ENCODING (major):** Before 2024-03-18, counts were per-direction; after, they are both directions combined. Same 'vehicles' column encodes different concepts.
- **INT-NO-JOIN-KEY (major):** No location data. A separate asset register is needed to map counters to air quality stations.

**Conditions:** (1) Access must be granted. (2) Counter-break adjustment method must be agreed. (3) Counter-location asset register must be sourced. (4) Direction-field handling resolved.

### link.data_open_air_chicago_hour_aggre_d4970b — not feasible
Chicago, US air-quality data. Three blockers: **ACC-UNREACHABLE** (host catalog.data.gov not allowlisted), **LIC-UNKNOWN** (no licence retrievable), **COV-GEO-MISMATCH** (Chicago vs Italy). Cannot be used by any route.

### link.europa_sdg_11_52_099aa6 — feasible with conditions
Annual national PM2.5-attributable premature deaths for Italy (2005–2023). CC BY 4.0. Supports N6 as annual national context. **COV-PARTIAL-WINDOW** flag dismissed because, as a 'could' need for context, the data ending in 2023 and missing 2004/2006 is acceptable. **Conditions:** (1) Attribution "© European Union, [year]. Source: Eurostat (SDG_11_52)" must accompany any output. (2) Methodology break pre/post 2007 must be documented. (3) 2004 and 2024–2025 not covered.

### link.uci_360 — feasible with conditions
Hourly readings from a multisensor device at road level in an unnamed Italian city, March 2004 – February 2005. Matches the prototype window exactly. Provides NO₂, T, RH for N1/N3. **Key flags:**
- **DQ-SENTINEL-VALUES (major):** Missing values encoded as -200 (17.5% of NO₂ rows, 90.2% of NMHC rows).
- **DQ-METADATA-CONTRADICTION (major):** Declared "has_missing_values: no" but uses -200 extensively.
- **INT-REPRESENTATIVENESS (major):** Single site, unnamed city — may not be Valdena.
- **FRS-STALE (major):** 21.5 years old — **dismissed** because staleness is acceptable for prototype/benchmark use per calibration rule 4.

**Conditions:** (1) Licence resolved (CC BY 4.0 declared but notes say "research purposes only, commercial purposes fully excluded" — legal review needed). (2) -200 sentinel values replaced with NULL. (3) City identity verified. (4) Single-site limitation documented.

### vendor.atmosdata_pro — not feasible
Vendor weather feed. Expired contract (AD-2021-114 ended 2025-12-31), API key revoked 2026-01-01, no renewal signed. Three blockers: LIC-UNKNOWN, LIC-AGREEMENT-NOT-ACTIVE, ACC-UNREACHABLE. Cannot be used. No conditions within project scope.

## 4. Red-flag register

| Source id | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| internal.airq.station_readings | ACC-RESTRICTED | major | auth_required=True, request to Environment Monitoring Unit not yet confirmed | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Catalog lists network active with no VR-03 closure; wiki states VR-03 switched off 2024-06-30 | judgement |
| internal.airq.station_readings | INT-NO-JOIN-KEY | major | Schema has station_id but no coordinates or location; no documented reference table | judgement |
| internal.clinic.patient_visits | ACC-RESTRICTED | major | auth_required=True, DPO approval required | rule |
| internal.clinic.patient_visits | GOV-PII | major | PII fields: patient_key, age_band, postcode | rule |
| internal.clinic.patient_visits | GOV-CONSENT-GAP | blocker | Wiki: "Patient-level visit records may not be used for this analysis" | judgement |
| internal.clinic.patient_visits | GOV-PURPOSE-LIMITATION | major | Policy limits purposes — patient-level not allowed | judgement |
| internal.clinic.resp_visits_daily | ACC-RESTRICTED | major | auth_required=True, request to Clinical Analytics not yet granted | rule |
| internal.clinic.resp_visits_daily | DQ-UNDOCUMENTED-SCHEMA | major | Diagnosis classification and district code system undocumented | judgement |
| internal.clinic.resp_visits_daily | INT-NO-JOIN-KEY | major | No crosswalk between districts and station/counter locations | judgement |
| internal.traffic.hourly_counts | ACC-RESTRICTED | major | auth_required=True, request to Mobility Office not yet granted | rule |
| internal.traffic.hourly_counts | DQ-METADATA-CONTRADICTION | major | Catalog omits counter replacement 2024-03-18; wiki documents it | judgement |
| internal.traffic.hourly_counts | DQ-SEMANTIC-ENCODING | major | Per-direction counts before 2024-03-18, combined after; same column | judgement |
| internal.traffic.hourly_counts | INT-NO-JOIN-KEY | major | No location data; asset register needed | judgement |
| link.uci_360 | DQ-SENTINEL-VALUES | major | -200 used for missing values in 17.5% of NO₂ rows and 90.2% of NMHC rows | judgement |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | Declared "has_missing_values: no" but -200 used extensively | judgement |
| link.uci_360 | INT-REPRESENTATIVENESS | major | Single-site, unnamed city may not be Valdena | judgement |
| link.uci_360 | FRS-STALE | major | 21.5 years old (dismissed: acceptable for prototype use) | rule |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | Data ends 2023, missing 2004, 2006 gaps (dismissed: acceptable for 'could' context need) | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | Host catalog.data.gov not allowlisted | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | No licence retrievable | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | Chicago (US) vs Italy | judgement |
| vendor.atmosdata_pro | LIC-UNKNOWN | blocker | No terms_url or docs_url in register | rule |
| vendor.atmosdata_pro | LIC-AGREEMENT-NOT-ACTIVE | blocker | Contract AD-2021-114 expired 2025-12-31, no renewal | rule |
| vendor.atmosdata_pro | ACC-UNREACHABLE | blocker | API key revoked 2026-01-01 | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | CC BY 4.0 requires attribution | rule |
| api.open_meteo_archive | LIC-MIXED | major | Upstream providers have different licence terms | rule |
| link.uci_360 | LIC-ATTRIBUTION | minor | CC BY 4.0 requires attribution | rule |
| link.europa_sdg_11_52_099aa6 | LIC-ATTRIBUTION | minor | CC BY 4.0 requires attribution | rule |

## 5. Conditions and owners

| Condition | Source(s) | Who can resolve it | Blocking which need |
|---|---|---|---|
| Access request granted | internal.airq.station_readings | Environment Monitoring Unit (Giulia Rossi) | N1 (production) |
| Station VR-03 gap from 2024-07-01 documented and handled | internal.airq.station_readings | Project team | N1 (production) |
| Station-location reference table sourced | internal.airq.station_readings | Environment Monitoring Unit | N1, N2 (spatial join) |
| Access request granted | internal.traffic.hourly_counts | Mobility Office (Luca Ferri) | N2 |
| Counter-break adjustment method agreed (2024-03-18) | internal.traffic.hourly_counts | Mobility Office / project team | N2 |
| Counter-location asset register sourced | internal.traffic.hourly_counts | Mobility Office (Luca Ferri) | N2 (spatial join) |
| Direction-field handling resolved | internal.traffic.hourly_counts | Mobility Office / project team | N2 |
| Access request granted | internal.clinic.resp_visits_daily | Clinical Analytics (Chiara Conti) | N4 |
| Diagnosis classification criteria documented and verified | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| District code system and boundary stability confirmed | internal.clinic.resp_visits_daily | Clinical Analytics / Data Protection Office | N4 |
| District-to-station-area crosswalk created | internal.clinic.resp_visits_daily | Project team | N4 (spatial join) |
| Attribution text placed | api.open_meteo_archive | Project team | N3 |
| Coordinates set to northern Italy | api.open_meteo_archive | Project team | N3 |
| Upstream licence mix reviewed by legal team | api.open_meteo_archive | Legal team | N3 |
| Licence ambiguity resolved (CC BY 4.0 vs "research only" note) | link.uci_360 | Legal team | N1 (prototype) |
| Sentinel value -200 handling implemented | link.uci_360 | Project team | N1 (prototype) |
| City identity verified (via De Vito et al. 2008 paper) | link.uci_360 | Project team | N1 (prototype) |
| Attribution placed | link.europa_sdg_11_52_099aa6 | Project team | N6 |
| Methodology break pre/post 2007 documented | link.europa_sdg_11_52_099aa6 | Project team | N6 |

## 6. Recommended next steps

1. **Raise access requests immediately** — all three internal sources (air quality, traffic, clinic daily) require formal access that has not been granted. Contact: Giulia Rossi (Environment Monitoring), Luca Ferri (Mobility Office), Chiara Conti (Clinical Analytics).
2. **Resolve the catalog–wiki conflict for station VR-03** — confirm the closure date and decide whether to drop that station or impute its missing 2024-07-01 to 2025-12-31 data.
3. **Source the station-location reference table** and the **counter-location asset register** — spatial joins between air quality, traffic and clinic data depend on both.
4. **Ask the Mobility Office** to document the counter-replacement adjustment method (per-direction vs combined direction) and provide the direction breakdown so the 2024-03-18 break can be handled.
5. **Ask Clinical Analytics** to document the diagnosis classification system (ICD-10 or local) and the district code enumeration with boundary stability notes.
6. **Ask legal to review two licence issues:** (a) the UCI dataset's conflicting "research only" restriction against the declared CC BY 4.0, and (b) Open-Meteo's mixed upstream licences for production use.
7. **Start prototyping now** on the UCI Air Quality dataset (link.uci_360) — handle the -200 sentinel values, verify the city identity, and document the single-site limitation. This can run in parallel with access requests.
8. **Configure Open-Meteo** with northern Italy coordinates (e.g. 45.46, 9.19) and verify hourly temperature/humidity for both windows.
9. **Once access is granted**, profile internal.airq.station_readings first (most critical for N1), then internal.traffic.hourly_counts and internal.clinic.resp_visits_daily.

## 7. Open questions for the human reviewer

1. The UCI Air Quality dataset comes from an unnamed "Italian city" — is there a known connection to Valdena, or should we treat it as a non-Valdena proxy for the prototype only?
2. The geographic coordinates for Open-Meteo were tested at Milan (45.46, 9.19) as a northern Italian city. What are Valdena's exact coordinates?
3. Station VR-03 stopped on 2024-06-30 — should we request a replacement station from the Environment Monitoring Unit, or plan to model without that station for the second half of the production window?
4. The clinic's district code system is undocumented — can Clinical Analytics provide the enumeration and confirm whether district boundaries changed between 2022 and 2025?
5. The DPO has already prohibited patient-level records — should we formally close N5 as out of scope, or is there a case for re-requesting under a different purpose?
6. Is the Eurostat PM2.5 mortality data (ending 2023) sufficient for context, or should we look for an alternative source covering 2024–2025?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-20T11:53:33Z (model DeepSeek-V4-Flash). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. The UCI Air Quality dataset comes from an unnamed "Italian city" — is there a known connection to Valdena, or should we treat it as a non-Valdena proxy for the prototype only?
2. The geographic coordinates for Open-Meteo were tested at Milan (45.46, 9.19) as a northern Italian city. What are Valdena's exact coordinates?
3. Station VR-03 stopped on 2024-06-30 — should we request a replacement station from the Environment Monitoring Unit, or plan to model without that station for the second half of the production window?
4. The clinic's district code system is undocumented — can Clinical Analytics provide the enumeration and confirm whether district boundaries changed between 2022 and 2025?
5. The DPO has already prohibited patient-level records — should we formally close N5 as out of scope, or is there a case for re-requesting under a different purpose?
6. Is the Eurostat PM2.5 mortality data (ending 2023) sufficient for context, or should we look for an alternative source covering 2024–2025?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
