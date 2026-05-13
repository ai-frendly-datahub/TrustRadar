from __future__ import annotations

from collections.abc import Iterable, Sequence
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Mapping

from radar_core.report_utils import (
    generate_index_html as _core_generate_index_html,
)
from radar_core.report_utils import (
    generate_report as _core_generate_report,
)

from .models import Article, CategoryConfig


def build_entity_cooccurrence_graph(
    entities_json: Sequence[Mapping[str, object]],
    *,
    max_nodes: int = 20,
) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    """Build a (node_counts, edge_counts) pair for the top max_nodes entities.

    Args:
        entities_json: list of per-article matched_entities dicts.
        max_nodes: keep only the top max_nodes entities by article frequency.

    Returns:
        node_counts: {entity_name: article_count}, sorted by count desc.
        edge_counts: {(name_a, name_b): cooccurrence_count} with a < b
                     (lexicographic) and both endpoints inside max_nodes.
    """
    node_counter: Counter[str] = Counter()
    for entry in entities_json:
        if not isinstance(entry, Mapping):
            continue
        for key in entry.keys():
            if isinstance(key, str) and key:
                node_counter[key] += 1

    top_nodes = [name for name, _ in node_counter.most_common(max_nodes)]
    kept = set(top_nodes)
    node_counts = {name: node_counter[name] for name in top_nodes}

    edge_counter: Counter[tuple[str, str]] = Counter()
    for entry in entities_json:
        if not isinstance(entry, Mapping):
            continue
        names = sorted(name for name in entry.keys() if isinstance(name, str) and name in kept)
        for a, b in combinations(names, 2):
            edge_counter[(a, b)] += 1

    edge_counts = dict(edge_counter)
    return node_counts, edge_counts


def build_entity_network_html(
    entities_json: Sequence[Mapping[str, object]],
    *,
    include_plotlyjs: bool = True,
    max_nodes: int = 20,
) -> str:
    """Render the entity co-occurrence graph as a Plotly HTML fragment.

    Returns a short empty-state HTML string when there is not enough data.
    """
    node_counts, edge_counts = build_entity_cooccurrence_graph(
        entities_json, max_nodes=max_nodes
    )
    if len(node_counts) < 2:
        return (
            '<div class="entity-network-empty">'
            "Not enough co-occurrence data to render the entity network."
            "</div>"
        )

    try:
        import plotly.graph_objects as go  # type: ignore[import-not-found]
    except Exception:
        # Plotly not installed; fall back to a static markup placeholder that
        # still contains the data so consumers can render later if needed.
        rows = "".join(
            f'<li data-count="{count}">{name}</li>'
            for name, count in node_counts.items()
        )
        return (
            '<div class="entity-network plotly-fallback">'
            '<ul class="entity-network-nodes">'
            f"{rows}"
            "</ul>"
            "</div>"
        )

    # Simple deterministic circular layout
    import math

    names = list(node_counts.keys())
    n = len(names)
    positions = {
        name: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
        for i, name in enumerate(names)
    }

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for (a, b), _ in edge_counts.items():
        ax, ay = positions[a]
        bx, by = positions[b]
        edge_x.extend([ax, bx, None])
        edge_y.extend([ay, by, None])

    node_x = [positions[name][0] for name in names]
    node_y = [positions[name][1] for name in names]
    node_sizes = [10 + (node_counts[name] ** 0.5) * 6 for name in names]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"width": 1, "color": "#888"},
            hoverinfo="none",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=names,
            textposition="top center",
            marker={"size": node_sizes, "color": "#1f77b4"},
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig.to_html(include_plotlyjs=include_plotlyjs, full_html=False)


def generate_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store=None,
) -> Path:
    """Generate HTML report (delegates to radar-core)."""
    articles_list = list(articles)
    plugin_charts = []

    # --- Universal plugins (entity heatmap + source reliability) ---
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

    # --- Entity Co-occurrence Network section ---
    entities_json = [
        article.matched_entities or {}
        for article in articles_list
    ]
    network_html = build_entity_network_html(entities_json, include_plotlyjs=False)
    extra_sections = [
        {
            "id": "entity-network",
            "aria_label": "Entity co-occurrence network",
            "title": "Entity Co-occurrence Network",
            "panel_title": "Entity Co-occurrence Network",
            "subtitle": "Entities that appear together in the same article",
            "badges": [],
            "body_html": f'<div class="network-wrap">{network_html}</div>',
        }
    ]

    return _core_generate_report(
        category=category,
        articles=articles_list,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
        extra_sections=extra_sections,
    )


def generate_index_html(
    report_dir: Path,
    summaries_dir: Path | None = None,
) -> Path:
    """Generate index.html (delegates to radar-core)."""
    radar_name = "Trust Radar"
    return _core_generate_index_html(report_dir, radar_name)
