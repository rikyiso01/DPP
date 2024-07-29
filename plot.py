from typer import Typer
from pathlib import Path
from networkx import Graph, draw, spring_layout, closeness_centrality
from tempfile import NamedTemporaryFile
from matplotlib.pyplot import savefig, show
from subprocess import run
from data import Data
from typing import Any, Optional

from paper import AnonymizedData

app = Typer()


@app.command()
def main(
    input: Path,
    out: Optional[str] = None,
    seed: int = 42,
    k: float = 1,
    anonymized: bool = False,
):
    model = AnonymizedData if anonymized else Data
    data = model.model_validate_json(input.read_text())
    graph: Graph[Any] = data.following
    pos = spring_layout(graph, k=k, seed=seed)
    centrality = [*closeness_centrality(graph).values()]
    draw(
        graph,
        pos,
        node_size=10,
        node_color=centrality,
        edge_color=(0.1, 0.5, 0.8, 0.3),
        linewidths=0.01,
        margins=(0, 0),
        arrowsize=3,
    )
    try:
        if out is None:
            with NamedTemporaryFile(delete=False, suffix=".svg") as tmp:
                out = tmp.name
        savefig(out)
        run(["xdg-open", out])
    except FileNotFoundError:
        show()


if __name__ == "__main__":
    app()
