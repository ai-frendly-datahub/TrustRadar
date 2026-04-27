from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from html import escape
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping

from radar_core.ontology import build_summary_ontology_metadata
from radar_core.report_utils import (
    generate_index_html as _core_generate_index_html,
)
from radar_core.report_utils import (
    generate_report as _core_generate_report,
)

from .models import Article, CategoryConfig


def build_entity_cooccurrence_graph(
    entities_json: Iterable[dict[str, list[str]]], *, max_nodes: int = 12
) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    node_counter: Counter[str] = Counter()
    article_entities: list[list[str]] = []

    for entities in entities_json:
        names = sorted(str(name) for name, values in entities.items() if values)
        if not names:
            continue
        article_entities.append(names)
        node_counter.update(names)

    selected_nodes = {name for name, _ in node_counter.most_common(max_nodes)}
    node_counts = {name: node_counter[name] for name in selected_nodes}
    edge_counter: Counter[tuple[str, str]] = Counter()
    for names in article_entities:
        filtered = sorted(name for name in names if name in selected_nodes)
        for left, right in combinations(filtered, 2):
            edge_counter[(left, right)] += 1

    return dict(sorted(node_counts.items(), key=lambda item: (-item[1], item[0]))), dict(edge_counter)


def build_entity_network_html(
    entities_json: Iterable[dict[str, list[str]]], *, include_plotlyjs: bool = True
) -> str:
    node_counts, edge_counts = build_entity_cooccurrence_graph(entities_json)
    if not node_counts or not edge_counts:
        return '<div class="empty-state">Not enough co-occurrence data</div>'

    nodes = list(node_counts)
    payload = {
        "nodes": nodes,
        "node_counts": node_counts,
        "edges": [
            {"source": left, "target": right, "weight": weight}
            for (left, right), weight in edge_counts.items()
        ],
    }
    plotly_loader = (
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        if include_plotlyjs
        else ""
    )
    labels = json.dumps(nodes, ensure_ascii=False)
    values = json.dumps([node_counts[node] for node in nodes], ensure_ascii=False)
    payload_json = json.dumps(payload, ensure_ascii=False)
    return (
        f'{plotly_loader}<div class="network-wrap"><div class="plotly-graph-div" id="entity-network"></div></div>'
        f'<script type="application/json" id="entity-network-data">{payload_json}</script>'
        '<script>'
        f'Plotly.newPlot("entity-network", [{{type:"bar", x:{labels}, y:{values}}}], '
        '{title:"Entity Co-occurrence Network"});'
        '</script>'
    )


def generate_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store=None,
    quality_report: Mapping[str, Any] | None = None,
) -> Path:
    """Generate HTML report (delegates to radar-core)."""
    articles_list = list(articles)
    plugin_charts = []
    extra_sections: list[dict[str, Any]] = []

    entity_maps = [article.matched_entities for article in articles_list if article.matched_entities]
    if entity_maps:
        plugin_charts.append(
            {
                "id": "entity-cooccurrence-network",
                "title": "Entity Co-occurrence Network",
                "config_json": json.dumps(
                    {"html": build_entity_network_html(entity_maps, include_plotlyjs=False)},
                    ensure_ascii=False,
                ),
            }
        )

    try:
        from radar_core.plugins.entity_heatmap import get_chart_config as _heatmap_config

        _heatmap = _heatmap_config(articles=articles_list)
        if _heatmap is not None:
            plugin_charts.append(_heatmap)
    except Exception:
        pass
    try:
        from radar_core.plugins.source_reliability import get_chart_config as _reliability_config

        _reliability = _reliability_config(store=store)
        if _reliability is not None:
            plugin_charts.append(_reliability)
    except Exception:
        pass
    if quality_report:
        extra_sections.append(_build_trust_quality_section(quality_report))

    return _core_generate_report(
        category=category,
        articles=articles_list,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
        extra_sections=extra_sections or None,
        ontology_metadata=build_summary_ontology_metadata(
            "TrustRadar",
            category_name=category.category_name,
            search_from=Path(__file__).resolve(),
        ),
    )


def generate_index_html(
    report_dir: Path,
    summaries_dir: Path | None = None,
) -> Path:
    """Generate index.html (delegates to radar-core)."""
    radar_name = "Trust Radar"
    return _core_generate_index_html(report_dir, radar_name)


def _build_trust_quality_section(quality_report: Mapping[str, Any]) -> dict[str, Any]:
    summary = quality_report.get("summary")
    summary_map = summary if isinstance(summary, Mapping) else {}
    sources = [row for row in _list(quality_report.get("sources")) if isinstance(row, Mapping)]
    events = [row for row in _list(quality_report.get("events")) if isinstance(row, Mapping)]
    flagged_sources = [
        row
        for row in sources
        if str(row.get("status")) in {"stale", "missing", "unknown_event_date"}
    ][:6]
    highlighted_events = events[:6]
    chips = [
        ("fresh", summary_map.get("fresh_sources", 0)),
        ("stale", summary_map.get("stale_sources", 0)),
        ("missing", summary_map.get("missing_sources", 0)),
        ("incidents", summary_map.get("incident_disclosure_events", 0)),
        ("status incidents", summary_map.get("status_page_incident_events", 0)),
        ("enforcement", summary_map.get("enforcement_action_events", 0)),
        ("complaints", summary_map.get("consumer_complaint_events", 0)),
        ("AI asset risks", summary_map.get("ai_asset_risk_events", 0)),
        ("services", summary_map.get("unique_service_count", 0)),
        ("needs official source", summary_map.get("official_confirmation_required_events", 0)),
    ]
    chip_html = "\n".join(
        f'<span class="chip"><strong>{escape(label)}</strong> {escape(str(value))}</span>'
        for label, value in chips
    )
    note = escape(str(quality_report.get("verification_scope_note") or ""))
    return {
        "id": "trust-quality",
        "title": "Trust Quality",
        "panel_title": "Incident and Verification Checks",
        "subtitle": "Freshness, disclosure status, enforcement outcomes, and source authority.",
        "badges": ["trust_quality.json", "incident", "verification"],
        "body_html": (
            f"<div class=\"inline-chips\">{chip_html}</div>"
            f"<p class=\"muted small\">{note}</p>"
            "<div><h3>Flagged Sources</h3>"
            f"{_render_quality_sources(flagged_sources)}"
            "</div>"
            "<div><h3>Tracked Events</h3>"
            f"{_render_trust_events(highlighted_events)}"
            "</div>"
        ),
    }


def _render_quality_sources(flagged_sources: list[Mapping[str, Any]]) -> str:
    if not flagged_sources:
        return '<p class="muted small">No stale or missing tracked sources in this run.</p>'

    items: list[str] = []
    for row in flagged_sources:
        source = escape(str(row.get("source", "")))
        status = escape(str(row.get("status", "")))
        model = escape(str(row.get("event_model", "")))
        age = row.get("age_days")
        age_text = "" if age is None else f", age {escape(str(age))}d"
        items.append(f"<li><strong>{source}</strong>: {status} ({model}{age_text})</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def _render_trust_events(events: list[Mapping[str, Any]]) -> str:
    if not events:
        return '<p class="muted small">No tracked trust events in this run.</p>'

    items: list[str] = []
    for event in events:
        title = escape(str(event.get("title", "")))
        model = escape(str(event.get("event_model", "")))
        source = escape(str(event.get("source", "")))
        details = _event_details(event)
        items.append(f"<li><strong>{model}</strong> {title} ({source}){details}</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def _event_details(event: Mapping[str, Any]) -> str:
    values: list[str] = []
    verification_state = str(event.get("verification_state") or "")
    role = str(event.get("verification_role") or "")
    statuses = _list(event.get("incident_status"))
    outcomes = _list(event.get("enforcement_outcomes"))
    asset_risks = _list(event.get("ai_asset_risks"))
    services = _list(event.get("affected_services")) or _list(event.get("service_ids"))
    if verification_state:
        values.append(f"state {escape(verification_state)}")
    if role:
        values.append(f"role {escape(role)}")
    if services:
        values.append("service " + escape(", ".join(str(item) for item in services)))
    if statuses:
        values.append("status " + escape(", ".join(str(item) for item in statuses)))
    if outcomes:
        values.append("outcome " + escape(", ".join(str(item) for item in outcomes)))
    if asset_risks:
        values.append("AI asset " + escape(", ".join(str(item) for item in asset_risks)))
    return "" if not values else ": " + "; ".join(values)


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
