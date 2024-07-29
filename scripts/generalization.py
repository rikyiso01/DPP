from __future__ import annotations
from collections import Counter
import random
from pandas import DataFrame

from collections.abc import Callable
from typing import Any
from random import randint
from datetime import date
from typer import Typer
from pathlib import Path
from data import Data, Gender
from faker import Faker


type Generalization[T] = Callable[[T, int], T]


def generalize[T](v: T, generalization: Generalization[T], steps: int) -> T:
    return generalization(v, steps)


def generalize_dataset(
    table: DataFrame[str, int, Any],
    g: dict[str, Generalization[Any]],
    s: dict[str, int],
) -> DataFrame[str, int, Any]:
    return table.apply(
        lambda row: [
            generalize(r, g[column], s[column]) for r, column in zip(row, table.columns)
        ]
    )


def generalize_cap(c: int, step: int):
    return c // 10**step * 10**step


def generalize_gender(g: Gender, step: int):
    if step == 1:
        return "*"
    else:
        return g


def generalize_address(a: str, step: int):
    for _ in range(step):
        *pieces, _ = a.split(",")
        a = ",".join(pieces)
    return a


def generalize_city(a: str, step: int):
    if step == 0:
        return a
    if step == 1:
        return a[:2].upper()
    return "*"


def generalize_phone_number(a: str, step: int):
    if step == 0:
        return a
    return a[:-step] + "*" * step  # We also hide the number of digits if step is high


def generalize_birth_date(b: date, step: int):
    if step >= 1:
        b = b.replace(day=1)
    if step >= 2:
        b = b.replace(month=1)
    if step >= 3:
        b = b.replace(year=1)
    return b


def substitute(v: list[str], f: Callable[[Faker], str], seed: int) -> list[str]:
    unique = {*v}
    faker = Faker(seed=seed)
    map: dict[str, str] = {u: f(faker) for u in unique}
    return [map[u] for u in v]


def perturbate[T](v: T, f: Callable[[T], T]) -> T:
    return f(v)


def perturbate_followers(v: int) -> int:
    return max(v + randint(-10, 10), 0)


EI: dict[str, Callable[[Faker], str]] = {
    "username": lambda f: f.user_name(),
    "name": lambda f: f.first_name(),
    "surname": lambda f: f.last_name(),
    "email": lambda f: f.email(),
}
QI = {
    "birth_date": (generalize_birth_date, 2),
    "gender": (generalize_gender, 1),
    "cap": (generalize_cap, 3),
    "address": (generalize_address, 1),
    "city": (generalize_city, 1),
    "phone_number": (generalize_phone_number, 5),
}
SD = {"followers": perturbate_followers}


def preprocessing(data: Data) -> DataFrame[str, int, Any]:
    users = data.users
    df: DataFrame[str, int, Any] = DataFrame([u.model_dump() for u in users])
    df["followers"] = [data.following.in_degree(u) for u in users]
    return df


def anonymize_data(
    data: DataFrame[str, int, Any], seed: int, k: int
) -> DataFrame[str, int, Any]:
    random.seed(seed)
    data = data.copy()
    for ei, f in EI.items():
        data[ei] = substitute([*data[ei]], f, seed)
    # data[[*QI]] = datafly(data, k)
    for qi, (f, steps) in QI.items():
        data[qi] = data[qi].apply(lambda v: generalize(v, f, steps))
    for sd, f in SD.items():
        data[sd] = data[sd].apply(lambda v: perturbate(v, f))
    return data


def datafly(data: DataFrame[str, int, Any], k: int):
    data = data[[*QI]].copy()
    frequencies = Counter(tuple(row) for _, row in data.iterrows())
    steps = {c: 0 for c in QI}
    while any(freq < k for freq in frequencies.values()) and len(frequencies) > k:
        qi = data.nunique().idxmax()
        steps[qi] += 1
        data[qi] = data[qi].apply(lambda v: generalize(v, QI[qi][0], steps[qi]))
        frequencies = Counter(tuple(row) for _, row in data.iterrows())
    to_suppress = {key for key, value in frequencies.items() if value < k}
    mask = [tuple(row) in to_suppress for _, row in data.iterrows()]
    frequencies = Counter(tuple(row) for _, row in data[mask].iterrows())
    while any(freq < k for freq in frequencies.values()):
        qi = data.nunique().idxmax()
        steps[qi] += 1
        data.loc[mask, qi] = data.loc[mask, qi].apply(
            lambda v: generalize(v, QI[qi][0], steps[qi])
        )
        frequencies = Counter(tuple(row) for _, row in data[mask].iterrows())
    print(steps)
    return data


app = Typer(pretty_exceptions_enable=False)


@app.command()
def main(input: Path, output: str, seed: int = 42, k: int = 2):
    users = Data.model_validate_json(input.read_text())
    anonymize_data(preprocessing(users), seed, k).to_csv(output, index=False)


if __name__ == "__main__":
    app()
