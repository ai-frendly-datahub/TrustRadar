from __future__ import annotations

import shutil
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import cast

import networkx as nx
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader

from .models import Article, CategoryConfig


DEFAULT_NETWORK_NODE_LIMIT = 80


_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
    )


def _copy_static_assets(report_dir: Path) -> None:
    src = _TEMPLATE_DIR / "static"
    dst = report_dir / "static"
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        _ = shutil.copytree(str(src), str(dst))


def generate_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
) -> Path:
    """Render a simple HTML report for the collected articles."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    articles_list = list(articles)
    entity_counts = _count_entities(articles_list)

    articles_json: list[dict[str, object]] = []
    entities_json: list[dict[str, list[str]]] = []
    for article in articles_list:
        matched_entities = article.matched_entities or {}
        article_data: dict[str, object] = {
            "title": article.title,
            "link": article.link,
            "source": article.source,
            "published": article.published.isoformat() if article.published else None,
            "published_at": article.published.isoformat() if article.published else None,
            "summary": article.summary,
            "matched_entities": matched_entities,
            "collected_at": article.collected_at.isoformat() if article.collected_at else None,
        }
        articles_json.append(article_data)
        entities_json.append(matched_entities)

    entity_network_html = build_entity_network_html(entities_json, include_plotlyjs="cdn")

    template = _get_jinja_env().get_template("report.html")
    rendered = template.render(
        category=category,
        articles=articles_list,
        articles_json=articles_json,
        entity_network_html=entity_network_html,
        generated_at=datetime.now(UTC),
        stats=stats,
        entity_counts=entity_counts,
        errors=errors or [],
    )
    _ = output_path.write_text(rendered, encoding="utf-8")

    now_ts = datetime.now(UTC)
    date_stamp = now_ts.strftime("%Y%m%d")
    dated_name = f"{category.category_name}_{date_stamp}.html"
    dated_path = output_path.parent / dated_name
    _ = dated_path.write_text(rendered, encoding="utf-8")

    _copy_static_assets(output_path.parent)

    return output_path


def _count_entities(articles: Iterable[Article]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for article in articles:
        for entity_name, keywords in (article.matched_entities or {}).items():
            counter[entity_name] += len(keywords)
    return counter


def _normalize_entity_name(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    return " ".join(text.split())


def build_entity_cooccurrence_graph(
    entities_json: list[dict[str, list[str]]],
    max_nodes: int = DEFAULT_NETWORK_NODE_LIMIT,
) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    frequency: Counter[str] = Counter()
    normalized_groups: list[list[str]] = []

    for entity_map in entities_json:
        unique_names: set[str] = set()
        for raw_name in entity_map.keys():
            normalized = _normalize_entity_name(raw_name)
            if normalized:
                unique_names.add(normalized)
        names = sorted(unique_names)
        if not names:
            continue
        frequency.update(names)
        normalized_groups.append(names)

    top_nodes = {
        name
        for name, _ in sorted(frequency.items(), key=lambda item: (-item[1], item[0]))[:max_nodes]
    }

    node_counts: Counter[str] = Counter()
    edge_counts: Counter[tuple[str, str]] = Counter()
    for names in normalized_groups:
        selected = sorted(name for name in names if name in top_nodes)
        if not selected:
            continue
        node_counts.update(selected)
        if len(selected) < 2:
            continue
        for left, right in combinations(selected, 2):
            edge_counts[(left, right)] += 1

    return dict(node_counts), dict(edge_counts)


def build_entity_network_html(
    entities_json: list[dict[str, list[str]]],
    include_plotlyjs: str | bool,
    max_nodes: int = DEFAULT_NETWORK_NODE_LIMIT,
) -> str:
    node_counts, edge_counts = build_entity_cooccurrence_graph(entities_json, max_nodes=max_nodes)
    if not node_counts:
        return (
            '<div class="network-empty">'
            "Not enough co-occurrence data to build an entity network."
            "</div>"
        )

    graph = nx.Graph()
    for node, count in node_counts.items():
        graph.add_node(node, frequency=count)

    for (left, right), weight in edge_counts.items():
        if left in node_counts and right in node_counts and left != right:
            graph.add_edge(left, right, weight=weight)

    if graph.number_of_nodes() == 1:
        raw_positions = nx.circular_layout(graph)
    else:
        raw_positions = nx.spring_layout(graph, seed=42, weight="weight")

    positions: dict[str, tuple[float, float]] = {
        node: (float(raw_positions[node][0]), float(raw_positions[node][1])) for node in node_counts
    }

    edge_x: list[float] = []
    edge_y: list[float] = []
    node_degree: Counter[str] = Counter()
    for left, right in graph.edges():
        left_pos = positions[left]
        right_pos = positions[right]
        edge_x.extend([left_pos[0], right_pos[0], float("nan")])
        edge_y.extend([left_pos[1], right_pos[1], float("nan")])
        node_degree[left] += 1
        node_degree[right] += 1

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        hoverinfo="skip",
        line={"width": 1.0, "color": "rgba(150,190,255,0.28)"},
    )

    max_frequency = max(node_counts.values())
    node_x: list[float] = []
    node_y: list[float] = []
    marker_sizes: list[float] = []
    marker_colors: list[int] = []
    labels: list[str] = []
    hover_text: list[str] = []

    ordered_nodes = sorted(node_counts.keys(), key=lambda name: (-node_counts[name], name.lower()))
    for node in ordered_nodes:
        frequency = node_counts[node]
        degree = node_degree[node]
        node_x.append(positions[node][0])
        node_y.append(positions[node][1])
        marker_sizes.append(12.0 + (frequency / max_frequency) * 24.0)
        marker_colors.append(degree)
        labels.append(node if len(node) <= 24 else f"{node[:21]}...")
        hover_text.append(f"{node}<br>Frequency: {frequency}<br>Connections: {degree}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=labels,
        textposition="top center",
        hoverinfo="text",
        hovertext=hover_text,
        marker={
            "size": marker_sizes,
            "color": marker_colors,
            "colorscale": [[0.0, "#19a7c3"], [0.5, "#33d6c5"], [1.0, "#f6c84c"]],
            "showscale": False,
            "line": {"width": 1.0, "color": "rgba(5,7,12,0.88)"},
            "opacity": 0.93,
        },
        textfont={"size": 10, "color": "rgba(233,238,251,0.88)"},
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"showgrid": False, "showticklabels": False, "zeroline": False},
        yaxis={"showgrid": False, "showticklabels": False, "zeroline": False},
    )

    return cast(
        str,
        fig.to_html(
            full_html=False,
            include_plotlyjs=include_plotlyjs,
            config={"displayModeBar": False, "responsive": True},
        ),
    )


def generate_index_html(report_dir: Path) -> Path:
    """Generate an index.html that lists all available report files."""
    report_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(
        [f for f in report_dir.glob("*.html") if f.name != "index.html"],
        key=lambda p: p.name,
    )

    reports: list[dict[str, str]] = []
    for html_file in html_files:
        name = html_file.stem
        display_name = name.replace("_report", "").replace("_", " ").title()
        reports.append({"filename": html_file.name, "display_name": display_name})

    template = _get_jinja_env().get_template("index.html")
    rendered = template.render(
        reports=reports,
        generated_at=datetime.now(UTC),
    )

    index_path = report_dir / "index.html"
    _ = index_path.write_text(rendered, encoding="utf-8")
    return index_path
