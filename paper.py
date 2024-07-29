from __future__ import annotations
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum, auto
from itertools import count
from typing import Any, Protocol, Self, override
from networkx import Graph, MultiDiGraph
from pydantic import TypeAdapter
from tqdm import tqdm
import networkx as nx

from data import User, Data, GraphOverlay
from typer import Typer


class Ordering(Protocol):
    def __lt__(self, other: Self, /) -> bool:
        ...


@dataclass
class Class[N]:
    id: int
    nodes: frozenset[N]

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return str(self.id)


@dataclass
class ClassGraphOverlay(GraphOverlay[Class[User]]):
    users: list[User]
    classes: list[Class[User]]

    @override
    @classmethod
    def _validate_field[
        V
    ](
        cls,
        field_name: str,
        annotation: type[V],
        data: object,
        prev_fields: dict[str, Any],
    ) -> V:
        if field_name != "classes":
            return super()._validate_field(field_name, annotation, data, prev_fields)
        classes = TypeAdapter(dict[int, list[str]]).validate_python(data)
        mapping: dict[str, User] = {u.username: u for u in prev_fields["users"]}
        return [
            Class(i, frozenset(mapping[username] for username in c))
            for i, c in sorted(classes.items())
        ]

    @override
    def _dump_field[V](self, field_name: str, annotation: type[V], data: V) -> object:
        if field_name != "classes":
            return super()._dump_field(field_name, annotation, data)
        return {c.id: [u.username for u in c.nodes] for c in self.classes}

    @override
    def _nodes_map(self) -> list[tuple[str, Class[User]]]:
        return [(str(c.id), c) for c in self.classes]

    @classmethod
    def from_graphs_list(
        cls,
        users: list[User],
        classes: list[Class[User]],
        graphs: Mapping[str, Graph[Any]],
    ) -> Self:
        return cls(users, classes, **graphs)


@dataclass
class AnonymizedData(ClassGraphOverlay):
    following: MultiDiGraph[Class[User]]


def divide_nodes[
    N
](
    V: Graph[N],
    m: int,
    ordering: Callable[[N], Ordering],
    progress: bool = True,
) -> list[frozenset[N]]:
    # O(|E||V|) + O(|V|log|V|)
    C: list[tuple[set[N], set[N]]] = []

    def safety_condition(c: tuple[set[N], set[N]], v: N) -> bool:  # O(|V[v]|)
        _, sc = c
        return not bool(sc & {*V[v], v})

    def insert(c: tuple[set[N], set[N]], v: N):  # O(|V[v]|)
        cls, sc = c
        cls.add(v)
        sc |= {*V[v]}
        sc.add(v)

    def create_new_class():  # O(1)
        c: tuple[set[N], set[N]] = (set(), set())
        C.append(c)
        return c

    # O(|V|log|V|)
    for v in tqdm(
        sorted(V, key=ordering), desc="creating classes", disable=not progress
    ):  # O(|V|)
        flag = True
        for c in C:  # O(|V|)
            if safety_condition(c, v) and len(c[0]) < m:  # O(|V[v]|)
                insert(c, v)
                flag = False
                break
        if flag:
            insert(create_new_class(), v)
    assert {*V} == {u for c, _ in C for u in c}
    return [frozenset(c) for c, _ in C]  # O(|V|)


def generate_uniform_lists[
    N
](
    classes: list[frozenset[N]],
    pattern: Collection[int],
    ordering: Callable[[N], Ordering],
) -> dict[N, Class[N]]:
    counter = count()
    return {
        u: Class(next(counter), generate_uniform_list(cls, u, pattern, ordering))
        for cls in classes
        for u in cls
    }


def generate_uniform_list[
    N
](
    C: frozenset[N],
    node: N,
    pattern: Collection[int],
    ordering: Callable[[N], Ordering],
) -> frozenset[N]:
    cls = sorted(C, key=ordering)
    index = cls.index(node)
    return frozenset(cls[(index + p) % len(cls)] for p in pattern)


def apply_uniform_lists[N](G: Graph[N], classes: dict[N, Class[N]]):
    return nx.relabel_nodes(G, classes)


def prefix_pattern(k: int):
    return range(k)


def ordering_function(u: User):
    return u.birth_date


def check_anonymized[N](G: Graph[N], classes: list[frozenset[N]]) -> bool:
    aux = {c: cls for cls in classes for c in cls}
    for v in G:
        interactions: set[frozenset[N]] = set()
        for w in G[v]:
            if aux[w] in interactions:
                return False
            interactions.add(aux[w])
    return True


def extract_interaction_graph[N](graphs: Iterable[Graph[N]]) -> Graph[N]:
    result: Graph[N] = Graph()
    for graph in graphs:
        result.add_edges_from(graph.edges())
    return result


def extract_interaction_graph_from_overlay[N](overlay: GraphOverlay[N]) -> Graph[N]:
    return extract_interaction_graph(overlay.all_graphs().values())


app = Typer(pretty_exceptions_enable=False)


class Operation(StrEnum):
    uniform_list = auto()
    partitioning = auto()


def anonymize_data(
    data: Data,
    operation: Operation,
    m: int,
    pattern: Collection[int],
    progress: bool = False,
) -> AnonymizedData:
    interaction_graph = extract_interaction_graph_from_overlay(data)
    classes = divide_nodes(interaction_graph, m, ordering_function, progress=progress)
    assert check_anonymized(interaction_graph, classes)
    match operation:
        case Operation.uniform_list:
            return anonymize_uniform_list(data, classes, pattern)
        case Operation.partitioning:
            return anonymize_partitioning(data, classes)


def anonymize_uniform_list(
    data: Data, classes: list[frozenset[User]], pattern: Collection[int]
) -> AnonymizedData:
    mapping = generate_uniform_lists(classes, pattern, ordering_function)
    new_graphs = {
        name: apply_uniform_lists(graph, mapping)
        for name, graph in data.all_graphs().items()
    }
    return AnonymizedData.from_graphs_list(data.users, [*mapping.values()], new_graphs)


def anonymize_partitioning(
    data: Data, classes: list[frozenset[User]]
) -> AnonymizedData:
    partitions = [Class(i, n) for i, n in enumerate(classes)]
    new_graphs = {
        name: partition_graph(graph, partitions)
        for name, graph in data.all_graphs().items()
    }
    return AnonymizedData.from_graphs_list(data.users, partitions, new_graphs)


def partition_graph[
    N
](G: Graph[N], partitions: list[Class[N]]) -> MultiDiGraph[Class[N]]:
    mapping = {u: partition for partition in partitions for u in partition.nodes}
    result: MultiDiGraph[Class[N]] = MultiDiGraph()
    result.add_nodes_from(mapping[u] for u in G)
    result.add_edges_from((mapping[u], mapping[v]) for u, v in G.edges())
    return result


@app.command()
def main(operation: Operation, input: str, output: str, m: int = 10, k: int = 10):
    data = Data.load(input)
    new_data = anonymize_data(
        data, operation, m=m, pattern=prefix_pattern(k), progress=True
    )
    new_data.dump(output)
    AnonymizedData.load(output)


if __name__ == "__main__":
    app()
