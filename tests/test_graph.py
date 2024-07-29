from networkx import Graph
from scripts.graph import check_strong, check_weak, anonymize

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

Gm = G.copy()
Gm.add_edge(3, 10)
Gm.add_edge(10, 5)


def test_check_weak():
    assert check_weak(G, 1, 1)
    assert not check_weak(G, 2, 1)
    assert not check_weak(G, 3, 1)
    assert not check_weak(G, 4, 1)
    assert not check_weak(G, 5, 1)
    assert not check_weak(G, 6, 1)

    assert check_weak(Gm, 1, 1)
    assert check_weak(Gm, 2, 1)
    assert check_weak(Gm, 3, 1)
    assert check_weak(Gm, 4, 1)
    assert not check_weak(Gm, 5, 1)
    assert not check_weak(Gm, 6, 1)
    assert not check_weak(Gm, 7, 1)


def test_strong_check():
    assert check_strong(G, Gm, 1, 1)
    assert check_strong(G, Gm, 2, 1)
    assert check_strong(G, Gm, 3, 1)
    assert not check_strong(G, Gm, 4, 1)
    assert not check_strong(G, Gm, 5, 1)
    assert not check_strong(G, Gm, 6, 1)
    assert not check_strong(G, Gm, 7, 1)


def test_check_anonymize():
    Ga = anonymize(G)
    assert check_weak(Ga, 2, 1)
    assert Ga != G
