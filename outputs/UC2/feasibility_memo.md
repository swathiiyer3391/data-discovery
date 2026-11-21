## 1. Executive summary

**Feasible with conditions** — all three must-needs can be met, but N2 (product code mapping) is the weakest link and requires manual help from the shop owner. The key facts driving the verdict:

1. **N1 (daily sales)** exists in a daily-grain internal table covering both windows, but has a 34-day gap (2024-02-05 to 2024-03-10) due to a till migration, and requires access approval from Retail Operations.
2. **N2 (product code mapping)** has no automated mapping — old codes (ending in L) were replaced on 2024-04-01, and matching can only be done by product name, which is not always unique.
3. **N3 (daily max temperature)** is fully covered by the free Open-Meteo archive API under CC BY 4.0, requiring attribution and exact shop coordinates.
4. **N4 (public holidays)** is met by the free Nager.Date API (MIT licence) at national level; regional holidays are not included.
5. **N5 (shop opening days & events)** is directly available from an internal shop calendar with no barriers.

## 2. Need coverage

| Need id | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Daily ice-cream sales by product | must | met_with_conditions | internal.sales.daily_by_product | 34-day gap (2024-02-05 to 2024-03-10) during till migration — no rows exist; product code change on 2024-04-01 requires join handling via product names |
| N2 | Mapping of product codes before and after the 2024 code change | must | partially_met | internal.sales.daily_by_product, internal.sales.products | No automated mapping exists between old (pre-2024-04) and new codes; matching by product name possible for uniquely-named products, but some names are not unique and require manual resolution |
| N3 | Daily maximum temperature | must | met_with_conditions | api.open_meteo_archive | None — covers both windows fully. Conditions: CC BY 4.0 attribution, verify exact shop coordinates, accept reanalysis latency for most recent days |
| N4 | Public holidays in Italy | should | met | api.nager_public_holidays | Only national public holidays covered; regional/provincial holidays (e.g. Veneto patron saint days) are not included |
| N5 | Shop opening days and local events | should | met | internal.store.calendar | None — source directly matches the need; local events are self-reported and may be incomplete |

## 3. Source assessments

### api.nager_public_holidays
**What it is:** MIT-licensed public API providing national public holidays for all countries.
**Verdict:** feasible. Returns 13–14 national holidays per year for Italy (2023–2026), daily grain, no access barriers. Only national holidays are covered — regional holidays for Veneto (where the shop is likely located) are not included. This is acceptable for a should-priority need.
**Key flags:** none.

### internal.store.calendar
**What it is:** Daily shop calendar with is_open (boolean) and event_name (free-text) columns, covering 2022-01-01 to present.
**Verdict:** feasible. Matches N5 exactly at daily grain for both windows. No access barriers (Open to analytics roles). Weekly refresh means the most recent week may be up to 5 days stale. Events are self-reported and may be incomplete.
**Key flags:** none.

### api.open_meteo_archive
**What it is:** Free, no-authentication API providing gap-free daily maximum temperature from ERA5/ERA5-Land reanalysis and ECMWF IFS for any lat/lon.
**Verdict:** feasible_with_conditions. Probes confirmed temperature_2m_max values for Verona (assumed location: 45.44, 10.99) across both windows. 
**Key flags with evidence:**
- **LIC-ATTRIBUTION** (minor): CC BY 4.0 requires attribution text: "Weather data by Open-Meteo.com" with link to https://open-meteo.com/.
- **LIC-MIXED** (major): Underlying sources use various licences (DWD: CC-BY, ECMWF: CC-BY, UK Met Office: CC-BY-SA, Copernicus: Licence, ItaliaMeteo-ARPAE: CC-BY), but the API output is offered under CC BY 4.0.
**Conditions:** (1) Include CC BY 4.0 attribution in any output. (2) Verify exact shop coordinates (assumed Verona 45.44, 10.99) before production use. (3) Note that reanalysis has a few days latency for the most recent data.

### internal.sales.daily_by_product
**What it is:** Daily units_sold and revenue_eur per product from the till system, covering 2022-01-01 to present, ~310k rows, 64 products.
**Verdict:** feasible_with_conditions. Core source for N1 covering both windows at daily grain.
**Key flags with evidence:**
- **ACC-RESTRICTED** (major): auth_required=True, classification=confidential, access request process = "Request to Retail Operations" (Marco Bianchi).
- **COV-PARTIAL-WINDOW** (major): Wiki till_migration_2024 confirms no rows exist from 2024-02-05 to 2024-03-10 (34 days) within the history window.
- **DQ-SEMANTIC-ENCODING** (major): Product codes ending in L were replaced on 2024-04-01; no mapping table exists. The same column uses two different code systems before and after this date.
**Conditions:** (1) Request access from Retail Operations. (2) Treat the 34-day gap as missing data (not zero sales). (3) For N2: join old and new codes by product name via sales.products, accepting some non-unique names require manual resolution.

### internal.sales.products
**What it is:** Current (post-2024) product catalogue: 64 rows, 3 columns (product_code, product_name, category). Static lookup, refreshed on change.
**Verdict:** feasible_with_conditions. Used alongside daily_by_product for N2.
**Key flags with evidence:**
- **ACC-RESTRICTED** (major): auth_required=True, classification=internal, but access is "Open to analytics roles" — less restrictive than daily_by_product.
- **DQ-SEMANTIC-ENCODING** (major): Only stores current (post-2024) codes; old codes are not present. The wiki product_codes_2024 confirms no mapping exists and product names are not always unique.
**Conditions:** (1) Must be combined with old codes from daily_by_product records before 2024-04-01, matched by product name. (2) Non-unique product names require manual resolution from the shop owner. (3) Last refreshed 2025-03-31 — verify any products added after that date are included.

## 4. Red-flag register

| Source id | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| internal.sales.daily_by_product | ACC-RESTRICTED | major | auth_required=True, classification=confidential, access.request_process='Request to Retail Operations' | rule |
| internal.sales.daily_by_product | COV-PARTIAL-WINDOW | major | Wiki till_migration_2024 confirms no rows from 2024-02-05 to 2024-03-10 (34 days) in history window | judgement |
| internal.sales.daily_by_product | DQ-SEMANTIC-ENCODING | major | Wiki product_codes_2024 (last_edited 2024-04-02): codes ending in L replaced on 2024-04-01, no mapping table exists | judgement |
| internal.sales.products | ACC-RESTRICTED | major | auth_required=True, classification=internal, access.request_process='Open to analytics roles' | rule |
| internal.sales.products | DQ-SEMANTIC-ENCODING | major | Wiki product_codes_2024 confirms this table only has current (post-2024) codes; old codes not stored | judgement |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | CC BY 4.0 requires attribution text: 'Weather data by Open-Meteo.com' with link | rule |
| api.open_meteo_archive | LIC-MIXED | major | Underlying data from DWD (CC-BY), ECMWF (CC-BY), UK Met Office (CC-BY-SA), Copernicus (Licence), ItaliaMeteo-ARPAE (CC-BY) | rule |

## 5. Conditions and owners

| Condition | Source(s) | Who can resolve it | Blocking which need |
|---|---|---|---|
| Request access from Retail Operations (Marco Bianchi) | internal.sales.daily_by_product | Marco Bianchi (Retail Operations steward) | N1, N2 |
| Treat 34-day till migration gap (2024-02-05 to 2024-03-10) as missing data | internal.sales.daily_by_product | Analytics team (documentation decision) | N1 |
| Join old and new product codes by product name — non-unique names need manual resolution | internal.sales.daily_by_product, internal.sales.products | Shop owner (resolve ambiguous name matches); Analytics team (create join) | N2 |
| Include CC BY 4.0 attribution in any output | api.open_meteo_archive | Analytics team | N3 |
| Verify exact shop coordinates (currently assuming Verona 45.44, 10.99) | api.open_meteo_archive | Client (shop owner) | N3 |
| Accept reanalysis latency for most recent days | api.open_meteo_archive | Analytics team (accept known limitation) | N3 |

## 6. Recommended next steps

1. **Raise access request** to Marco Bianchi (Retail Operations) for `internal.sales.daily_by_product` — this blocks both N1 and N2.
2. **Ask the shop owner** for:
   - The exact latitude/longitude of the shop (to replace the Verona assumption for the weather API).
   - A manual mapping of any product names that are not unique between the old (pre-2024-04) and new (post-2024-04) code systems — this will resolve the main risk for N2.
3. **Confirm the shop owner can provide the 34-day gap information** — is the gap truly missing data, or were sales recorded in a backup system during the till migration?
4. **Once access and coordinates are confirmed**, profile the following sources in this order:
   - `internal.sales.daily_by_product` — the core N1 source with the most conditions.
   - `internal.sales.products` — to build the code mapping alongside daily_by_product.
   - `api.open_meteo_archive` — low-risk, but verify coordinates first.
5. **Set up the Nager.Date API** and `internal.store.calendar` — these are low-risk and can run in parallel.

## 7. Open questions for the human reviewer

1. The shop's location is assumed to be Verona (45.44, 10.99) based on "northern Italy" and the business brief. Can the shop owner confirm the exact coordinates?
2. The 34-day gap (2024-02-05 to 2024-03-10) is documented as missing till data. Were sales during this period recorded in any backup system or paper log that could be reconstructed?
3. How many product names are non-unique in the product catalogue? The shop owner will need to help resolve these — can they confirm this is feasible?
4. The Nager.Date API only covers national holidays. Are Veneto-regional holidays (e.g. the Feast of Saint Mark) important for this analysis, or is the national-level coverage sufficient?
5. Can Marco Bianchi (Retail Operations) be contacted directly for the access request, or is there a formal ticketing process?

---

## Human review gate

Draft generated by the discovery agents for UC2 on 2026-11-20T18:20:18Z (model DeepSeek-V4-Flash). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. 1. The shop's location is assumed to be Verona (45.44, 10.99) based on "northern Italy" and the business brief. Can the shop owner confirm the exact coordinates?
2. 2. The 34-day gap (2024-02-05 to 2024-03-10) is documented as missing till data. Were sales during this period recorded in any backup system or paper log that could be reconstructed?
3. 3. How many product names are non-unique in the product catalogue? The shop owner will need to help resolve these — can they confirm this is feasible?
4. 4. The Nager.Date API only covers national holidays. Are Veneto-regional holidays (e.g. the Feast of Saint Mark) important for this analysis, or is the national-level coverage sufficient?
5. 5. Can Marco Bianchi (Retail Operations) be contacted directly for the access request, or is there a formal ticketing process?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
