"""Browser-based article collection for JavaScript-rendered sources.

Uses the 2-pass hybrid collection pattern:
    Pass 1 (collector.py): RSS/API sources -> ThreadPoolExecutor (parallel)
    Pass 2 (this module):  JS/browser sources -> Playwright (sequential)

Playwright is an optional dependency. If ``radar-core[browser]`` is not
installed, this module degrades gracefully -- returning empty results with
a descriptive error string so the caller can log a warning and continue.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import structlog

from .models import Article


if TYPE_CHECKING:
    from .models import Source

logger = structlog.get_logger()

_BROWSER_COLLECTION_AVAILABLE = False
try:
    _module = importlib.import_module("radar_core.browser_collector")
    _core_collect = _module.collect_browser_sources

    _BROWSER_COLLECTION_AVAILABLE = True
except ImportError:
    _core_collect = None  # type: ignore[assignment]


def collect_browser_sources(
    sources: list[Source],
    category: str,
    *,
    timeout: int = 15_000,
    health_db_path: str | None = None,
) -> tuple[list[Article], list[str]]:
    """Collect articles from JavaScript-rendered sources via Playwright.

    Wraps :func:`radar_core.browser_collector.collect_browser_sources` and
    converts the returned ``radar_core.models.Article`` instances into local
    ``Article`` instances for pipeline compatibility.

    Args:
        sources: Source objects with ``type`` in ``("javascript", "browser")``.
        category: Category name stamped onto every collected article.
        timeout: Default Playwright page-load timeout in milliseconds.
        health_db_path: Optional path to crawl-health DuckDB file.

    Returns:
        ``(articles, errors)`` -- local Article list and human-readable error
        strings.  On failure the articles list is empty and errors explains why.
    """
    if not sources:
        return [], []

    if not _BROWSER_COLLECTION_AVAILABLE or _core_collect is None:
        logger.warning(
            "browser_collection_unavailable",
            reason="radar_core.browser_collector not installed",
            source_count=len(sources),
            hint="pip install 'radar-core[browser]'",
        )
        return [], [
            f"Browser collection unavailable for {len(sources)} JS source(s). "
            "Install radar-core[browser]."
        ]

    try:
        source_dicts: list[dict[str, Any]] = [
            {"name": s.name, "type": s.type, "url": s.url, "config": dict(s.config)}
            for s in sources
        ]
        core_articles, errors = _core_collect(
            sources=source_dicts,
            category=category,
            timeout=timeout,
            health_db_path=health_db_path,
        )
        retry_sources = _sources_with_errors(source_dicts, errors)
        if retry_sources:
            retry_articles, retry_errors = _core_collect(
                sources=retry_sources,
                category=category,
                timeout=timeout,
                health_db_path=health_db_path,
            )
            retried_names = {str(source["name"]) for source in retry_sources}
            core_articles.extend(retry_articles)
            errors = [
                error
                for error in errors
                if not _error_matches_any_source(error, retried_names)
            ]
            errors.extend(retry_errors)
    except ImportError:
        logger.warning(
            "playwright_not_installed",
            source_count=len(sources),
            hint="pip install 'radar-core[browser]'",
        )
        return [], [
            f"Playwright not installed for {len(sources)} JS source(s). "
            "Install radar-core[browser]."
        ]
    except Exception as exc:
        logger.error(
            "browser_collection_failed",
            error=str(exc),
            source_count=len(sources),
        )
        return [], [f"Browser collection failed: {exc}"]

    local_articles: list[Article] = []
    for article in core_articles:
        local_articles.append(
            Article(
                title=article.title,
                link=article.link,
                summary=article.summary,
                published=article.published,
                source=article.source,
                category=article.category or category,
            )
        )

    if local_articles:
        logger.info(
            "browser_collection_complete",
            article_count=len(local_articles),
            error_count=len(errors),
        )

    return local_articles, errors


def _sources_with_errors(
    source_dicts: list[dict[str, Any]],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not errors:
        return []
    return [
        source
        for source in source_dicts
        if _error_matches_source(source_name=str(source["name"]), errors=errors)
    ]


def _error_matches_source(*, source_name: str, errors: list[str]) -> bool:
    return any(error.startswith(f"{source_name}:") for error in errors)


def _error_matches_any_source(error: str, source_names: set[str]) -> bool:
    return any(error.startswith(f"{source_name}:") for source_name in source_names)
