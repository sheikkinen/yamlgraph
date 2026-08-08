"""FR-782 — Wikidata topic-label resolution (C-4).

Standard-library HTTP only, batched at 50 Q-IDs, disk-cached under the
output directory, and degrading to bare Q-IDs when offline. A missing
label is a missing label: it is never invented and never silently
replaced with a neighbouring language.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path

from .models import TopicRow

logger = logging.getLogger(__name__)

WIKIDATA_BATCH_SIZE = 50
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
CACHE_FILENAME = "wikidata-labels.json"

Fetcher = Callable[[Sequence[str], str], dict[str, str]]


def _cache_path(cache_dir: Path | str) -> Path:
    directory = Path(cache_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    return directory / CACHE_FILENAME


def _load_cache(cache_dir: Path | str) -> dict[str, str]:
    path = _cache_path(cache_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_cache(cache_dir: Path | str, cache: dict[str, str]) -> None:
    _cache_path(cache_dir).write_text(
        json.dumps(cache, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def http_fetch(qids: Sequence[str], language: str) -> dict[str, str]:
    """Fetch labels for one batch via the Wikidata API (stdlib urllib)."""
    query = urllib.parse.urlencode(
        {
            "action": "wbgetentities",
            "ids": "|".join(qids),
            "props": "labels",
            "languages": language,
            "format": "json",
        }
    )
    url = f"{WIKIDATA_API}?{query}"
    request = urllib.request.Request(  # noqa: S310 — fixed https API endpoint
        url, headers={"User-Agent": "yamlgraph-self-portrait-example/1.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
        data = json.loads(response.read().decode("utf-8"))
    labels: dict[str, str] = {}
    for qid, entity in data.get("entities", {}).items():
        label = entity.get("labels", {}).get(language, {}).get("value")
        if label:
            labels[qid] = label
    return labels


def resolve_labels(
    qids: Sequence[str],
    cache_dir: Path | str,
    language: str = "en",
    fetch: Fetcher | None = None,
) -> dict[str, str]:
    """Resolve Q-IDs to labels; cache hits never touch the network.

    Offline or HTTP failure degrades to the labels already known — the
    caller keeps bare Q-IDs for the rest (never a fabricated label).
    """
    fetcher = fetch or http_fetch
    cache = _load_cache(cache_dir)
    resolved = {
        qid: cache[f"{language}:{qid}"] for qid in qids if f"{language}:{qid}" in cache
    }
    missing = [qid for qid in qids if qid not in resolved]
    if not missing:
        return resolved

    for start in range(0, len(missing), WIKIDATA_BATCH_SIZE):
        batch = missing[start : start + WIKIDATA_BATCH_SIZE]
        try:
            fetched = fetcher(batch, language)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            logger.warning(
                "Wikidata unreachable (%s) — keeping bare Q-IDs for %d topic(s)",
                exc,
                len(batch),
            )
            break
        resolved.update(fetched)
        cache.update({f"{language}:{qid}": label for qid, label in fetched.items()})

    _save_cache(cache_dir, cache)
    return resolved


def apply_labels(topics: Sequence[TopicRow], labels: dict[str, str]) -> list[TopicRow]:
    """Attach resolved labels; unresolved topics keep `label is None`."""
    return [
        topic.model_copy(update={"label": labels.get(topic.topic_id)})
        for topic in topics
    ]
