# Step 0 — Setup and tooling checks

**Date:** 2026-11-19
**Model in use:** DeepSeek-V4-Flash
**Use case:** UC1 — Air quality and traffic

## Python environment
- Python 3.12.4 (detected)
- Virtual environment: not activated (system Python used)
- `pip install -r requirements.txt`: anthropic, jsonschema, pytest installed

## Gateway credentials
| Variable | Set? |
|---|---|
| `ANTHROPIC_BASE_URL` | ✅ Yes |
| `ANTHROPIC_AUTH_TOKEN` | ✅ Yes |
| `ANTHROPIC_MODEL` | ✅ Yes |

## Pytest results

### `tests/test_tools_offline.py` — ✅ PASSES
_No failures._

### `tests/test_agent_loop.py` — ✅ PASSES
_No failures._

### `tests/test_learner_gaps.py` — ❌ 20 FAILURES (expected)
These are all the learner gaps (G1, G3, G4, G5, G6) which are not yet implemented:

| Gap | Tests failed | Reason |
|---|---|---|
| **G1** (licence extraction) | 10 | `extract_licence` raises `NotImplementedTool` |
| **G3** (JSON-stat summary) | 2 | `jsonstat_summary` raises `NotImplementedTool` |
| **G4** (rules: temporal coverage, grain, metadata contradiction, evaluation) | 7 | `rule_*` functions raise `NotImplementedError` |
| **G5** (calibration rules) | 1 | `risk_assessor.md` G5 comment not written |
| **G6** (allowlist) | 1 | `ec.europa.eu` not in allowlist for Eurostat |

**Summary:** 32 passed, 20 failed (all expected learner TODOs).

## Tool smoke tests (offline, no LLM)

### `search_internal_catalog` — ✅
Ran `search_internal_catalog '{"query": "air quality"}' --use-case UC1`
Returned `{"hits": []}` (no lexical match in catalog — expected before Scout).

### `inspect_dataset_link` — ✅
Ran `inspect_dataset_link '{"url": "https://archive.ics.uci.edu/dataset/360/air+quality"}' --use-case UC1`
Returned full UCI dataset metadata (link_type: `uci_dataset_page`, 15 variables, 9358 instances).
Licence extraction shows `NotImplementedTool` (G1).

### `list_external_register` — ✅
Ran `list_external_register '{}' --use-case UC1`
Returned 4 sources: Open-Meteo, Nager.Date, policy.open_data_links, and the expired vendor AtmosData Pro.

## Notes
- Open-Meteo default lat/lng points to Lisbon (38.72, -9.14). The client is in northern Italy. This must be updated per README section 8.
- Allowlist currently has `archive.ics.uci.edu`, Open-Meteo, Nager.Date, GitHub. `ec.europa.eu` and `catalog.data.gov` are missing (G6).