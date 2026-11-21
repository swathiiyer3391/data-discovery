"""Licence and structured-metadata extraction from dataset landing pages."""
from __future__ import annotations

import json
import re

def jsonld_datasets(html: str) -> list[dict]:
    """Return every schema.org Dataset object embedded as JSON-LD in a page.

    Many portals (Kaggle, Zenodo, data.gov, Hugging Face, Dataverse, CKAN sites) embed one.
    It is the most reliable machine-readable description of a dataset when it exists.
    """
    found = []
    for m in re.finditer(r"""(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>""", html):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and "Dataset" in str(item.get("@type", "")):
                found.append(item)
    return found


def summarise_jsonld_dataset(d: dict) -> dict:
    """Keep the fields that matter for discovery, clipped for the model."""
    def name_of(v):
        if isinstance(v, list):
            return [name_of(x) for x in v][:5]
        if isinstance(v, dict):
            return v.get("name") or v.get("url") or v.get("@id")
        return v

    def clip(v, n=600):
        v = re.sub(r"<[^>]+>", " ", str(v)) if v is not None else None
        return None if v is None else (" ".join(v.split())[:n])

    dist = d.get("distribution") or []
    dist = dist if isinstance(dist, list) else [dist]
    return {
        "name": d.get("name"), "description": clip(d.get("description")),
        "license": d.get("license"), "creator": name_of(d.get("creator")), "publisher": name_of(d.get("publisher")),
        "datePublished": d.get("datePublished"), "dateModified": d.get("dateModified"),
        "temporalCoverage": d.get("temporalCoverage"), "spatialCoverage": name_of(d.get("spatialCoverage")),
        "isAccessibleForFree": d.get("isAccessibleForFree"), "keywords": clip(d.get("keywords"), 300),
        "variableMeasured": name_of(d.get("variableMeasured")),
        "distribution": [{k: x.get(k) for k in ("contentUrl", "encodingFormat", "fileFormat", "contentSize", "requiresSubscription", "name")
                          if isinstance(x, dict) and x.get(k) is not None} for x in dist[:10]],
    }


# ---------------------------------------------------------------------------
# G1: find the licence of ANY dataset from its landing page
# ---------------------------------------------------------------------------
# Order of evidence: JSON-LD "license" (string URL, or {"name", "url"}) first; then links to
# creativecommons.org / opendatacommons.org / nationalarchives.gov.uk (OGL) / choosealicense.com;
# then sentences such as "licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license".
# jsonld defaults to jsonld_datasets(html) when None. Never guess: return None values when unsure.

# Mapping from URL patterns or text to normalised licence names.
# Order matters: more specific patterns come first (e.g. "by-nc-sa" before "by-nc").
_LICENCE_PATTERNS: list[tuple[str, str]] = [
    # CC 4.0 variants
    (r"creativecommons\.org/licenses/by-nc-sa/4\.0", "CC BY-NC-SA 4.0"),
    (r"creativecommons\.org/licenses/by-nc-nd/4\.0", "CC BY-NC-ND 4.0"),
    (r"creativecommons\.org/licenses/by-sa/4\.0",   "CC BY-SA 4.0"),
    (r"creativecommons\.org/licenses/by-nc/4\.0",   "CC BY-NC 4.0"),
    (r"creativecommons\.org/licenses/by-nd/4\.0",   "CC BY-ND 4.0"),
    (r"creativecommons\.org/licenses/by/4\.0",      "CC BY 4.0"),
    # CC 3.0 variants
    (r"creativecommons\.org/licenses/by-nc-sa/3\.0", "CC BY-NC-SA 3.0"),
    (r"creativecommons\.org/licenses/by-sa/3\.0",    "CC BY-SA 3.0"),
    (r"creativecommons\.org/licenses/by-nc/3\.0",    "CC BY-NC 3.0"),
    (r"creativecommons\.org/licenses/by/3\.0",       "CC BY 3.0"),
    # CC0
    (r"creativecommons\.org/publicdomain/zero/1\.0", "CC0 1.0"),
    (r"choosealicense\.com/licenses/cc0-1\.0",       "CC0 1.0"),
    # ODbL
    (r"opendatacommons\.org/licenses/odbl/1\.0",     "ODbL 1.0"),
    # OGL
    (r"nationalarchives\.gov\.uk/doc/open-government-licence/version/3", "OGL v3.0"),
    (r"nationalarchives\.gov\.uk/doc/open-government-licence/version/2", "OGL v2.0"),
    # MIT
    (r"choosealicense\.com/licenses/mit",            "MIT"),
    # Apache-2.0
    (r"choosealicense\.com/licenses/apache-2\.0",    "Apache-2.0"),
]

# Text patterns for sentences that name a licence.
_LICENCE_TEXT_PATTERNS: list[tuple[str, str]] = [
    (r"CC BY-NC-SA 4\.0",       "CC BY-NC-SA 4.0"),
    (r"CC BY-NC-ND 4\.0",       "CC BY-NC-ND 4.0"),
    (r"CC BY-SA 4\.0",          "CC BY-SA 4.0"),
    (r"CC BY-NC 4\.0",          "CC BY-NC 4.0"),
    (r"CC BY-ND 4\.0",          "CC BY-ND 4.0"),
    (r"CC BY 4\.0",             "CC BY 4.0"),
    (r"CC BY-NC-SA 3\.0",       "CC BY-NC-SA 3.0"),
    (r"CC BY-SA 3\.0",          "CC BY-SA 3.0"),
    (r"CC BY 3\.0",             "CC BY 3.0"),
    (r"CC0 1\.0",               "CC0 1.0"),
    (r"ODbL 1\.0",              "ODbL 1.0"),
    (r"Open Government Licence v3\.0", "OGL v3.0"),
    (r"Open Government Licence v2\.0", "OGL v2.0"),
    (r"MIT\b",                  "MIT"),
    (r"Apache-2\.0",            "Apache-2.0"),
    (r"Apache 2\.0",            "Apache-2.0"),
]


def _url_to_licence_name(url: str) -> str | None:
    """Match a URL against known licence patterns and return the normalised name."""
    for pattern, name in _LICENCE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return name
    return None


def _text_to_licence_name(text: str) -> str | None:
    """Match text against known licence name patterns."""
    for pattern, name in _LICENCE_TEXT_PATTERNS:
        if re.search(pattern, text):
            return name
    return None


def _extract_from_jsonld(jsonld: list[dict]) -> dict | None:
    """Try to extract licence from JSON-LD Dataset objects.

    Returns dict with licence_name, licence_url, snippet, found_in or None.
    """
    for ds in jsonld:
        lic = ds.get("license")
        if lic is None:
            continue
        if isinstance(lic, str):
            # String URL
            name = _url_to_licence_name(lic)
            snippet = lic
            return {
                "licence_name": name,
                "licence_url": lic if lic.startswith("http") else None,
                "snippet": lic[:400],
                "found_in": "json-ld",
            }
        if isinstance(lic, dict):
            name = lic.get("name", "")
            url = lic.get("url", "")
            if name and name.lower() == "unknown":
                # "Unknown" is explicitly not a licence
                url_val = url if url.startswith("http") else None
                return {
                    "licence_name": None,
                    "licence_url": url_val,
                    "snippet": name[:400],
                    "found_in": "json-ld",
                }
            if name:
                normalised = _text_to_licence_name(name)
                url_val = url if url.startswith("http") else None
                return {
                    "licence_name": normalised or name,
                    "licence_url": url_val,
                    "snippet": name[:400],
                    "found_in": "json-ld",
                }
            if url:
                name = _url_to_licence_name(url)
                if name:
                    return {
                        "licence_name": name,
                        "licence_url": url,
                        "snippet": url[:400],
                        "found_in": "json-ld",
                    }
    return None


def _extract_from_links(html: str) -> dict | None:
    """Search <a> tag hrefs for known licence URLs."""
    for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>', html, re.IGNORECASE):
        href = m.group(1)
        name = _url_to_licence_name(href)
        if name:
            # Grab a short text snippet from around the link
            start = max(0, m.start() - 80)
            end = min(len(html), m.end() + 80)
            snippet = re.sub(r"<[^>]+>", " ", html[start:end]).strip()
            snippet = " ".join(snippet.split())[:400]
            return {
                "licence_name": name,
                "licence_url": href,
                "snippet": snippet,
                "found_in": "link",
            }
    return None


def _extract_from_text(html: str) -> dict | None:
    """Search for licence sentences in visible text."""
    # Remove tags to get plain text
    text = re.sub(r"<[^>]+>", " ", html)
    text = " ".join(text.split())

    for pattern, name in _LICENCE_TEXT_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            snippet = text[start:end].strip()[:400]
            # Try to also extract a URL from nearby
            url = None
            # Look for a URL within 100 chars of the match
            nearby = text[max(0, m.start() - 100):min(len(text), m.end() + 100)]
            url_match = re.search(r'https?://[^\s\)\]}>"\']+', nearby)
            if url_match:
                candidate = url_match.group(0)
                if any(d in candidate for d in
                       ["creativecommons", "opendatacommons", "nationalarchives",
                        "choosealicense"]):
                    url = candidate
            return {
                "licence_name": name,
                "licence_url": url,
                "snippet": snippet,
                "found_in": "text",
            }
    return None


def extract_licence(html: str, jsonld: list[dict] | None = None) -> dict:
    """Find the licence of a dataset from its landing page.

    Priority: JSON-LD → link → text.  Returns exactly the four keys:
    licence_name, licence_url, snippet, found_in.
    """
    # Default return for "no licence found"
    empty = {"licence_name": None, "licence_url": None, "snippet": None, "found_in": None}

    if jsonld is None:
        jsonld = jsonld_datasets(html)

    # 1. JSON-LD
    result = _extract_from_jsonld(jsonld)
    if result is not None:
        return result

    # 2. Links
    result = _extract_from_links(html)
    if result is not None:
        return result

    # 3. Text sentences
    result = _extract_from_text(html)
    if result is not None:
        return result

    return empty
