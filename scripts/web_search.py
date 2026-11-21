#!/usr/bin/env python3
"""
Web search script for the Data Discovery Agent (Step 2b).

Sends a search query to a chat-completions endpoint that supports
web_search_options, and prints the answer text followed by citation URLs.
Uses only the Python standard library — no extra dependencies.

Usage:
    python scripts/web_search.py "<query>"
"""

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/web_search.py \"<query>\"", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]

    # ── Required environment variables ──────────────────────────────────
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")

    missing = []
    if not base_url:
        missing.append("ANTHROPIC_BASE_URL")
    if not token:
        missing.append("ANTHROPIC_AUTH_TOKEN")

    if missing:
        print(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Set them and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Model ───────────────────────────────────────────────────────────
    model = os.environ.get("WEB_SEARCH_MODEL", "gemini-3.8-flash")

    # ── Build the request ───────────────────────────────────────────────
    # The base URL has no /v1 suffix. Append /v1/chat/completions per spec.
    url = f"{base_url}/v1/chat/completions"

    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    req = Request(url, data=body, headers=headers, method="POST")

    # ── Send ────────────────────────────────────────────────────────────
    try:
        with urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(
            f"HTTP {e.code} from gateway: {error_body}",
            file=sys.stderr,
        )
        sys.exit(1)
    except URLError as e:
        print(f"Request failed: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Response error: {e}", file=sys.stderr)
        sys.exit(1)

    # ── Extract and print output ────────────────────────────────────────
    try:
        choice = raw["choices"][0]
        answer = choice["message"]["content"]
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(answer)
    except (KeyError, IndexError) as e:
        print(
            f"Unexpected response structure (missing {e}): "
            f"{json.dumps(raw, indent=2)[:2000]}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Print citation URLs ─────────────────────────────────────────────
    citations = []

    # Check inside the message
    msg = choice.get("message", {})
    for citation in msg.get("citations", []):
        if isinstance(citation, str):
            citations.append(citation)
        elif isinstance(citation, dict):
            url_str = citation.get("url") or citation.get("link") or citation.get("source")
            if url_str:
                citations.append(url_str)

    # Some providers return citations at the top level
    if not citations:
        for citation in raw.get("citations", []):
            if isinstance(citation, str):
                citations.append(citation)
            elif isinstance(citation, dict):
                url_str = citation.get("url") or citation.get("link") or citation.get("source")
                if url_str:
                    citations.append(url_str)

    # Vertex AI grounding metadata (likely has citations)
    if not citations:
        grounding_list = raw.get("vertex_ai_grounding_metadata", [])
        if isinstance(grounding_list, list):
            for grounding in grounding_list:
                if not isinstance(grounding, dict):
                    continue
                for sources in grounding.get("groundingChunks", []):
                    if isinstance(sources, dict):
                        for chunk in sources.get("chunks", []):
                            if isinstance(chunk, dict):
                                uri = chunk.get("uri") or chunk.get("url")
                                if uri:
                                    citations.append(uri)
                                # web source
                                web = chunk.get("web", {})
                                if isinstance(web, dict):
                                    uri = web.get("uri") or web.get("url")
                                    if uri:
                                        citations.append(uri)
                # Also check groundingSupports
                for support in grounding.get("groundingSupports", []):
                    if isinstance(support, dict):
                        for segment in support.get("segments", []):
                            if isinstance(segment, dict):
                                context = segment.get("context", {})
                                if isinstance(context, dict):
                                    doc = context.get("documentMetadata", {})
                                    if isinstance(doc, dict):
                                        uri = doc.get("uri") or doc.get("url")
                                        if uri:
                                            citations.append(uri)

    # vertex_ai_url_context_metadata — sometimes URLs are here
    if not citations:
        url_ctx = raw.get("vertex_ai_url_context_metadata", [])
        if isinstance(url_ctx, list):
            for entry in url_ctx:
                if isinstance(entry, dict):
                    uri = entry.get("uri") or entry.get("url")
                    if uri:
                        citations.append(uri)
    if not citations:
        cit_meta = raw.get("vertex_ai_citation_metadata", [])
        if isinstance(cit_meta, list):
            for entry in cit_meta:
                if isinstance(entry, dict):
                    uri = entry.get("uri") or entry.get("URL") or entry.get("url")
                    if uri:
                        citations.append(uri)
                    # Some entries nest citations
                    for sub_key in ["citations", "sources", "references"]:
                        for sub in entry.get(sub_key, []):
                            if isinstance(sub, str) and sub.startswith("http"):
                                citations.append(sub)
                            elif isinstance(sub, dict):
                                u = sub.get("uri") or sub.get("URL") or sub.get("url")
                                if u:
                                    citations.append(u)
            for entry in cit_meta:
                if isinstance(entry, dict):
                    uri = entry.get("uri") or entry.get("URL") or entry.get("url")
                    if uri:
                        citations.append(uri)
                    # Some entries nest citations
                    for sub_key in ["citations", "sources", "references"]:
                        for sub in entry.get(sub_key, []):
                            if isinstance(sub, str) and sub.startswith("http"):
                                citations.append(sub)
                            elif isinstance(sub, dict):
                                u = sub.get("uri") or sub.get("URL") or sub.get("url")
                                if u:
                                    citations.append(u)
        elif isinstance(cit_meta, dict):
            for citation in cit_meta.get("citations", []):
                uri = citation.get("uri") or citation.get("URL") or citation.get("url")
                if uri:
                    citations.append(uri)

    # Some return them as annotations
    if not citations:
        for usage in raw.get("usage", {}).get("annotations", []):
            if isinstance(usage, dict):
                for ann_type in ["citations", "urls", "links", "sources"]:
                    for item in usage.get(ann_type, []):
                        if isinstance(item, str) and item.startswith("http"):
                            citations.append(item)

    # Final fallback: extract https URLs directly from the answer text
    if not citations:
        import re as _re
        found_urls = _re.findall(r'https?://[^\s\)\]}>\"\']+', answer)
        # Filter out duplicates and obviously non-citation URLs (code snippets, common infrastructure)
        seen = set()
        for u in found_urls:
            u_clean = u.rstrip(".,;:!?")
            if u_clean in seen:
                continue
            seen.add(u_clean)
            # Exclude obvious test/example URLs
            if any(skip in u_clean for skip in ["example.com", "localhost", "127.0.0.1"]):
                continue
            citations.append(u_clean)

    if citations:
        print("\n--- CITATIONS ---")
        for c in citations:
            print(c)
    else:
        print("\n[No citation URLs found in response]", file=sys.stderr)


if __name__ == "__main__":
    main()