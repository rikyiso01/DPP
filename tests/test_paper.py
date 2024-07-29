from __future__ import annotations
from collections import Counter
from pprint import pprint
from networkx import DiGraph, Graph, MultiDiGraph
import networkx as nx
from paper import (
    Class,
    apply_uniform_lists,
    check_anonymized,
    divide_nodes,
    extract_interaction_graph,
    generate_uniform_lists,
    partition_graph,
    prefix_pattern,
)

INTERACTIONS = [
    DiGraph({"v1": ["v2"], "v2": ["v1", "v7"], "v7": ["v2"]}),
    DiGraph({"v1": ["v2"], "v2": ["v1"]}),
    DiGraph({"v3": ["v4", "v5"], "v4": ["v3", "v5"], "v5": ["v3", "v4"]}),
    DiGraph({"v4": ["v5"], "v5": ["v4"], "v6": ["v7"], "v7": ["v6"]}),
]

G = DiGraph(
    {
        "v1": ["v2"],
        "v2": ["v1", "v7"],
        "v3": ["v4", "v5"],
        "v4": ["v3", "v5"],
        "v5": ["v3", "v4"],
        "v6": ["v7"],
        "v7": ["v2", "v6"],
    }
)

C1 = Class(1, frozenset(["v1", "v2", "v3"]))
C2 = Class(2, frozenset(["v4", "v5"]))
C3 = Class(3, frozenset(["v6", "v7"]))
Gm = MultiDiGraph(
    {
        C1: [
            C1,
            C1,
            C2,
            C2,
            C3,
        ],
        C2: [
            C1,
            C1,
            C2,
            C2,
        ],
        C3: [
            C1,
            C3,
            C3,
        ],
    }
)
Gm_CLASSES = [
    C1,
    C2,
    C3,
]

U1 = Class(1, frozenset(["v1", "v4", "v6"]))
U2 = Class(2, frozenset(["v2", "v5"]))
U3 = Class(3, frozenset(["v3", "v7"]))
U4 = Class(4, frozenset(["v1", "v4", "v6"]))
U5 = Class(5, frozenset(["v2", "v5"]))
U6 = Class(6, frozenset(["v1", "v4", "v6"]))
U7 = Class(7, frozenset(["v3", "v7"]))
Gm2 = DiGraph(
    {
        U1: [
            U2,
        ],
        U2: [U1, U7],
        U3: [U4, U5],
        U4: [U3, U5],
        U5: [U3, U4],
        U6: [U7],
        U7: [U6, U2],
    }
)
Gm2_CLASSES = [
    frozenset(["v1", "v4", "v6"]),
    frozenset(["v2", "v5"]),
    frozenset(["v3", "v7"]),
]
Gm2_CLASSES2 = {f"v{i}": v for i, v in enumerate([U1, U2, U3, U4, U5, U6, U7], start=1)}


def test_divide_nodes():
    classes = divide_nodes(G, 10, lambda v: v)
    assert check_anonymized(G, classes)


def test_extract_interaction_graph():
    assert sorted(
        sorted(e) for e in extract_interaction_graph(INTERACTIONS).edges()
    ) == sorted(sorted(e) for e in Graph(G).edges())


def test_partition1():
    actual = partition_graph(G, Gm_CLASSES)
    pprint(Counter(actual.edges()))
    pprint(Counter(Gm.edges()))
    assert Counter(actual.edges()) == Counter(Gm.edges())


def test_partition2():
    actual = partition_graph(INTERACTIONS[0], Gm_CLASSES)
    expected = MultiDiGraph(
        {
            C1: [C1, C1, C3],
            C3: [C1],
        }
    )
    pprint(Counter(actual.edges()))
    pprint(Counter(expected.edges()))
    assert Counter(actual.edges()) == Counter(expected.edges())


def test_generate_uniform_list():
    mapping = generate_uniform_lists(Gm2_CLASSES, prefix_pattern(10), lambda x: x)
    actual = Counter(m.nodes for m in mapping.values())
    expected = Counter(m.nodes for m in Gm2_CLASSES2.values())
    assert actual == expected


def test_apply_uniform_list():
    actual = apply_uniform_lists(G, Gm2_CLASSES2)
    assert sorted(actual.edges()) == sorted(Gm2.edges())


def test_check_anonymized():
    assert check_anonymized(G, Gm2_CLASSES)
