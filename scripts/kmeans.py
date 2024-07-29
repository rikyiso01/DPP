#!/bin/env python3
from __future__ import annotations
import random
import matplotlib.pyplot as plt
from collections.abc import Sequence, Collection
from typing import Protocol, Self
from functools import reduce
from pathlib import Path
from data import Data
from typer import Typer
from dataclasses import dataclass
from subprocess import run


class Vector(Protocol):
    def __sub__(self, other: Self, /) -> Self:
        ...

    def __add__(self, other: Self, /) -> Self:
        ...

    def __abs__(self) -> float:
        ...

    def __truediv__(self, other: int, /) -> Self:
        ...


def distance[T: Vector](p1: T, p2: T):
    return abs(p1 - p2)


def mean[T: Vector](p: Collection[T]) -> T | None:
    result: T | None = reduce(lambda acc, x: acc + x if acc is not None else x, p, None)
    if result is None:
        return None
    return result / len(p)


def kmeans[T: Vector](points: Sequence[T], k: int):
    centroids = random.sample(points, k=k)  # k centroidi
    old_clusters: Sequence[int | None] = [None] * len(points)

    while True:
        clusters = [
            min(range(k), key=lambda x: abs(points[i] - centroids[x]))
            for i in range(len(points))
        ]

        # Per ogni singolo cluster, aggiorno il centroide
        for i in range(k):
            # array che contiene tutti i punti che hanno come cluster di appartenenza
            # il cluster i-esimo
            center = mean([points[j] for j in range(len(points)) if clusters[j] == i])
            # If the cluster is empty we insert a random point into it
            if center is None:
                center = random.choice(points)
            centroids[i] = center

        if clusters == old_clusters:
            return clusters
        old_clusters = clusters


app = Typer()


@dataclass
class Point(Vector):
    x: float
    y: float

    def __sub__(self, other: Self, /) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other: Self, /) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __abs__(self) -> float:
        return abs(self.x**2 + self.y**2) ** 0.5

    def __truediv__(self, other: int, /) -> Point:
        return Point(self.x / other, self.y / other)


@app.command()
def main(input: Path, output: str, k: int = 3, seed: int = 42):
    random.seed(seed)
    data = Data.model_validate_json(input.read_text())
    in_degree = data.following.in_degree()
    out_degree = data.following.out_degree()
    degrees: list[Point] = [Point(in_degree[u], out_degree[u]) for u in data.following]
    clusters = kmeans(degrees, k)
    plt.scatter(
        [d.x for d in degrees], [d.y for d in degrees], c=[c / k for c in clusters]
    )
    plt.yscale("log")
    plt.xscale("log")
    plt.savefig(output)
    try:
        run(["xdg-open", output])
    except FileNotFoundError:
        plt.show()


if __name__ == "__main__":
    app()
