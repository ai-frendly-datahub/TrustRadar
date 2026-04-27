from __future__ import annotations

from trustradar import reporter


def test_build_entity_cooccurrence_graph_limits_top_nodes() -> None:
    entities_json = [
        {"Data Breach": ["breach"], "Credential Stuffing": ["stuffing"]},
        {
            "Data Breach": ["breach"],
            "Credential Stuffing": ["stuffing"],
            "Phishing": ["phishing"],
        },
        {"Data Breach": ["breach"]},
    ]

    node_counts, edge_counts = reporter.build_entity_cooccurrence_graph(entities_json, max_nodes=2)

    assert node_counts == {"Data Breach": 3, "Credential Stuffing": 2}
    assert edge_counts == {("Credential Stuffing", "Data Breach"): 2}


def test_build_entity_network_html_returns_empty_state() -> None:
    html = reporter.build_entity_network_html([], include_plotlyjs=False)

    assert "Not enough co-occurrence data" in html


def test_build_entity_network_html_renders_plotly_markup() -> None:
    entities_json = [
        {"Data Breach": ["breach"], "Credential Stuffing": ["stuffing"]},
        {"Data Breach": ["breach"], "Supply Chain": ["supply"]},
    ]

    html = reporter.build_entity_network_html(entities_json, include_plotlyjs=False)

    assert "Plotly.newPlot" in html
    assert "plotly-graph-div" in html
    assert "Data Breach" in html
