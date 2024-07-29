from __future__ import annotations
from tqdm import tqdm
from typer import Typer
from faker import Faker
import random
from networkx import DiGraph, scale_free_graph, selfloop_edges
from pathlib import Path
from data import Gender, User, Data

typer = Typer()

GENDERS = {Gender.MALE: 0.45, Gender.FEMALE: 0.45, Gender.NON_BINARY: 0.45}


def random_gender() -> Gender:
    (result,) = random.choices(
        [*Gender], k=1, weights=[GENDERS[gender] for gender in Gender]
    )
    return result


def profile(faker: Faker):
    return User(
        username=faker.unique.user_name(),
        name=faker.first_name(),
        surname=faker.last_name(),
        birth_date=faker.date_of_birth(),
        gender=random_gender(),
        cap=int(faker.postcode()),
        address=faker.street_address(),
        city=faker.city(),
        phone_number=faker.unique.phone_number().removeprefix("+39 "),
        email=faker.unique.email(),
    )


def generate_following(
    users: list[User],
    seed: int,
    alpha: float,
    beta: float,
    gamma: float,
    delta_in: float,
    delta_out: float,
):
    multigraph = scale_free_graph(
        n=len(users),
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        delta_in=delta_in,
        delta_out=delta_out,
        seed=seed,
    )
    assert len(multigraph) == len(users)
    graph = DiGraph(
        {users[id]: [users[i] for i in multigraph[id]] for id in multigraph}
    )
    graph.remove_edges_from(selfloop_edges(graph))
    return graph


def generate_data(
    n: int,
    seed: int,
    alpha: float,
    beta: float,
    gamma: float,
    delta_in: float,
    delta_out: float,
    progress: bool = True,
) -> Data:
    random.seed(seed)
    faker = Faker("it_IT", seed=seed)
    users = [
        profile(faker)
        for _ in tqdm(range(n), desc="generating users", disable=not progress)
    ]
    return Data(
        users=users,
        following=generate_following(
            users,
            seed=seed,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            delta_in=delta_in,
            delta_out=delta_out,
        ),
    )


@typer.command()
def main(
    out: Path,
    seed: int = 42,
    alpha: float = 0.41,
    beta: float = 0.54,
    gamma: float = 0.05,
    delta_in: float = 0.2,
    delta_out: float = 0,
    n: int = 10**4,
):
    data = generate_data(
        seed=seed,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        delta_in=delta_in,
        delta_out=delta_out,
        n=n,
    )
    out.write_text(data.model_dump_json())


if __name__ == "__main__":
    typer()
