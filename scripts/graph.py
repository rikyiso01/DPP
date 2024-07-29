#!/bin/python3
from __future__ import annotations
from networkx import Graph
from typing import Any
from typer import Typer
import matplotlib.pyplot as plt
import networkx as nx
from tempfile import NamedTemporaryFile
from subprocess import run
from data import Data
from traceback import print_exc


def check_weak(G: Graph[Any], k: int, l: int):
    # check the definition of all the vertices in V
    return all(sum(len({*G[v]} & {*G[u]}) >= l for u in G if u != v) >= k for v in G)


def check_strong(G: Graph[Any], Gm: Graph[Any], k: int, l: int):
    return all(sum(len({*G[v]} & {*Gm[u]}) >= l for u in G if u != v) >= k for v in G)


# Function to implement Linear-time weak (2, 1)-anonymization
def deficit_assignment[N](G: Graph[N]) -> dict[N, int]:
    unmarked = {u for u in G if G.degree(u) in [1, 2]}
    with_deficit: set[N] = set()
    while unmarked:
        u = unmarked.pop()
        to_mark: set[N] = set()
        to_mark |= condition_8(G, u)
        to_mark |= condition_9(G, u)
        for v in G[u]:
            if u == v:
                continue
            to_mark |= condition_1(G, u, v)
            to_mark |= condition_5(G, u, v)
            for w in G[v]:
                if w == v or w == u:
                    continue
                to_mark |= condition_2(G, u, v, w)
                to_mark |= condition_4(G, u, v, w)
                for x in G[w]:
                    if x in [u, v, w]:
                        continue
                    to_mark |= condition_3(G, u, v, w, x)
                    to_mark |= condition_6(G, u, v, w, x)
                    to_mark |= condition_7(G, u, v, w, x)
        with_deficit |= to_mark
        unmarked -= to_mark
    return {u: int(u in with_deficit) for u in G}


# For an isolated edge uv, we assign deficit 1
# to u and deficit 1 to v; it may be that both
# edges will be added at u
def condition_1[N](G: Graph[N], u: N, v: N) -> set[N]:
    if G.degree(u) == 1 and G.degree(v) == 1:
        return {u, v}
    else:
        return set()


# For an isolated path uvw, we assign deficit 1 to v.
def condition_2[N](G: Graph[N], u: N, v: N, w: N) -> set[N]:
    if G.degree(u) == 1 and G.degree(v) == 2 and G.degree(w) == 1:
        return {v}
    else:
        return set()


# For an isolated path uvwx, we assign deficit 1 to v and deficit 1 to w.
def condition_3[N](G: Graph[N], u: N, v: N, w: N, x: N) -> set[N]:
    if G.degree(u) == 1 and G.degree(v) == 2 and G.degree(w) == 2 and G.degree(x) == 1:
        return {v, w}
    else:
        return set()


# For a subgraph consisting of a path uvw
# with adjacent vertices attached to w, we assign deficit 1 to v.
# Note: the definition doesn't provide any other information about the degree of u and v; so we do nothing
def condition_4[N](G: Graph[N], u: N, v: N, w: N) -> set[N]:
    if G.degree(w) > 1:
        return {v}
    else:
        return set()


# For a component uvXi with vertex u having
# degree one with vertex v connected to a set
# of vertices Xi such that each x ∈ Xi has degree 1 (and no other vertices) assign deficit
# 1 to v. This component corresponds to an
# isolated star centered at v.
def condition_5[N](G: Graph[N], u: N, v: N) -> set[N]:
    if G.degree(u) == 1 and G.degree(v) > 1:
        if all(G.degree(x) == 1 for x in G[v]):
            return {v}
    return set()


# For a component consisting of a square
# uvwx (isolated square), we assign deficit 1
# to u and deficit 1 to w; it may be that the
# two edges will be added at u and v, or that
# u and w will be joined.
def condition_6[N](G: Graph[N], u: N, v: N, w: N, x: N) -> set[N]:
    if (
        G.degree(u) == 2
        and G.degree(v) == 2
        and G.degree(w) == 2
        and G.degree(x) == 2
        and x in G[u]
    ):
        return {u, w}
    return set()


# For a subgraph consisting of a square uvwx
# with edges (one or more) uxi coming out of
# the square, we assign deficit 1 to v.
def condition_7[N](G: Graph[N], u: N, v: N, w: N, x: N) -> set[N]:
    if x in G[u] and G.degree(u) > 2:
        return {v}
    return set()


# For a subgraph consisting of squares
# uv1wx1, uv2wx2, ..., uvjwxj , we assign
# deficit 1 to one of the vi’s.
def condition_8[N](G: Graph[N], u: N) -> set[N]:
    ws = {w for v in G[u] for w in G[v]}
    result: set[N] = set()
    for w in ws:
        result |= condition_8_inner(G, u, w)
    return result


def condition_8_inner[N](G: Graph[N], u: N, w: N) -> set[N]:
    for vi in G[u]:
        if w not in G[vi]:
            continue
        for xi in G[w]:
            if u not in G[xi]:
                continue
            return {vi}
    return set()


# For a subgraph consisting of a vertex
# u adjacent to vertices xi of degree 1 and to
# a vertex y of degree 2, assign deficit 1 to y.
def condition_9[N](G: Graph[N], u: N) -> set[N]:
    if G.degree(u) < 2:
        return set()
    ys = {y for y in G[u] if G.degree(y) == 2}
    if len(ys) != 1:
        return set()
    (y,) = ys
    for xi in G[u]:
        if xi == y:
            continue
        if G.degree(xi) != 1:
            return set()
    return {y}


# Function to implement Linear-time weak (2, 1)-anonymization
# Note: (*) the condition stated as "True" refers to the statement from the paper:
# "– in some case other than an isolated edge uv", case that we have already considered in deficit assignment
def deficit_matching[N](G: Graph[N], deficit: dict[N, int]):
    m = sum(deficit.values())
    to_pair = {u for u, d in deficit.items() if d != 0}
    if m % 2 == 0 and (m >= 4 or (m == 2 and True)):  # (*) see above
        match(G, to_pair)
    if m % 2 == 1:
        r = to_pair.pop()
        match(G, to_pair)
        G.add_edge(r, {u for u in G if G.degree(u) == 2 and u != r}.pop())
    isolated_vertices(G)


def special_case1[N](G: Graph[N]):
    isolated_edges = {
        (u, v) for u in G for v in G[u] if condition_1(G, u, v)
    }  # if condition_1 applies, we have isolated_edges
    while len(isolated_edges) > 1:
        u, v = isolated_edges.pop()
        ui, vi = isolated_edges.pop()
        G.add_edge(u, ui)
        G.add_edge(v, ui)
    if isolated_edges:
        u, v = isolated_edges.pop()
        r = ({*G} - {u, v}).pop()
        G.add_edge(u, r)
        G.add_edge(v, r)


def special_case2[N](G: Graph[N]):
    isolated_star = {
        (u, v) for u in G for v in G[u] if condition_5(G, u, v)
    }  # if condition_1 applies, we have isolated_stars
    # The paper is not clear about the case with multiple isolated starts as remaining
    # Then we decided to connect two stars because their center has 1 to 1 deficits and both would decrease to 0, like the normal case
    while len(isolated_star) > 1:
        u, v = isolated_star.pop()
        ui, vi = isolated_star.pop()
        G.add_edge(v, vi)
    if isolated_star:
        _, v = isolated_star.pop()
        G.add_edge(G[v][1], G[v][0])


def isolated_vertices[N](G: Graph[N]):
    isolated_vertices: set[N] = {u for u in G if G.degree(u) == 0}
    while len(isolated_vertices) >= 6:
        u, v, w, ui, vi, wi, *remaining = isolated_vertices
        isolated_vertices = {*remaining}
        G.add_edge(u, v)
        G.add_edge(u, w)
        G.add_edge(u, ui)
        G.add_edge(ui, vi)
        G.add_edge(ui, wi)
    while isolated_vertices:
        v = isolated_vertices.pop()
        G.add_edge(v, {u for u in G if G.degree(u) == 2}.pop())


# Function to match two non-adjacent vertices with non-zero deficies
def match[N](G: Graph[N], to_pair: set[N]):
    while to_pair:
        u = to_pair.pop()
        aux = to_pair.copy()
        while True:
            v = aux.pop()
            if v not in G[u]:
                break
        to_pair.remove(v)
        G.add_edge(u, v)


def anonymize[N](input: Graph[N]) -> Graph[N]:
    G = input.copy()
    deficit = deficit_assignment(G)
    special_case1(G)
    special_case2(G)
    deficit_matching(G, deficit)
    isolated_vertices(G)
    return G


app = Typer()


@app.command()
def main():
    G = Graph(
        {
            1: [2, 3],
            2: [1, 3],
            3: [1, 2, 4],
            4: [3, 5],
            5: [4, 6],
            6: [5, 7, 8, 9, 10],
            7: [6],
            8: [6],
            9: [6],
            10: [6],
        }
    )

    print("Input graph G")
    for k in range(1, 6):
        weak = check_weak(G, k, 1)
        print(f"G is ({k},{1})-anonymous", weak)
        assert weak == (k < 2)

    """
    if G is (k,l) anonymous then is also (1, l)-anonymous, ..., (k-1, anonymous)
    """

    Gm = G.copy()
    Gm.add_edge(3, 10)
    Gm.add_edge(10, 5)

    # k = 5
    print()
    print("(4,1)-anonymous transformation of G")
    for k in range(1, 7):
        weak = check_weak(Gm, k, 1)
        print(f"Gm is ({k},{1})-anonymous", weak)
        assert weak == (k < 5)

    print()
    print("(4,1)-anonymous transformation of G")
    for k in range(1, 6):
        weak = check_strong(G, Gm, k, 1)
        print(f"Gm is ({k},{1})-strong-anonymous", weak)
        assert weak == (k < 4)

    Ga = anonymize(G)
    nx.draw(Ga)
    with NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        plt.savefig(tmp.name)
    try:
        run(["xdg-open", tmp.name])
    except FileNotFoundError:
        plt.show()

    print()
    print("Input graph G after (2,1)-anonymization")
    for k in range(1, 6):
        weak = check_weak(Ga, k, 1)
        print(f"Ga is ({k},{1})-anonymous", weak)
        if k < 3:
            assert weak
    assert Ga != G


if __name__ == "__main__":
    app()
