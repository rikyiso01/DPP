from abc import abstractmethod
from dataclasses import dataclass
from datetime import date
from json import dump, dumps, load, loads
from pydantic import (
    TypeAdapter,
    BaseModel,
)
from networkx import DiGraph, Graph
import networkx as nx
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, Self, get_type_hints, override

if not TYPE_CHECKING:
    DiGraph.__class_getitem__ = lambda _: DiGraph
    Graph.__class_getitem__ = lambda _: Graph


class Gender(StrEnum):
    MALE = auto()
    FEMALE = auto()
    NON_BINARY = auto()


type ID = str


class User(BaseModel):
    username: ID  # EI
    name: str  # EI
    surname: str  # EI
    birth_date: date  # QI
    gender: Gender  # QI
    cap: int  # QI
    address: str  # QI
    city: str  # QI
    phone_number: str  # QI
    email: str  # EI

    @property
    def age(self):
        return (date.today() - self.birth_date).days // 365

    def __hash__(self):
        return hash(self.username)


class CustomModel:
    @classmethod
    def load(cls, file: str) -> Self:
        with open(file, "rt") as f:
            return cls.model_validate(load(f))

    @classmethod
    def model_validate(cls, data: object) -> Self:
        assert isinstance(data, dict)
        annotations: dict[str, type[object]] = get_type_hints(cls)
        kwargs: dict[str, object] = {}
        for field, annotation in annotations.items():
            kwargs[field] = cls._validate_field(field, annotation, data[field], kwargs)
        return cls(**kwargs)

    @classmethod
    def model_validate_json(cls, json: str) -> Self:
        return cls.model_validate(loads(json))

    def model_dump(self) -> dict[str, Any]:
        annotations: dict[str, type[object]] = get_type_hints(self.__class__)
        result: dict[str, object] = {}
        for field, annotation in annotations.items():
            input: object = getattr(self, field)
            result[field] = self._dump_field(field, annotation, input)

        return result

    @classmethod
    def graph_fields(cls) -> list[str]:
        annotations: dict[str, type[object]] = get_type_hints(cls)
        return [
            field
            for field, annotation in annotations.items()
            if issubclass(annotation, Graph)
        ]

    def model_dump_json(self) -> str:
        return dumps(self.model_dump())

    def dump(self, file: str):
        with open(file, "wt") as f:
            dump(self.model_dump(), f)

    @classmethod
    @abstractmethod
    def _validate_field[
        T
    ](
        cls,
        field_name: str,
        annotation: type[T],
        data: object,
        prev_fields: dict[str, Any],
        /,
    ) -> T:
        ...

    @abstractmethod
    def _dump_field[
        T
    ](self, field_name: str, annotation: type[T], data: T, /) -> object:
        ...


class GraphOverlay[T](CustomModel):
    @classmethod
    def load(cls, file: str) -> Self:
        with open(file, "rt") as f:
            return cls.model_validate(load(f))

    @classmethod
    @override
    def model_validate(cls, data: object) -> Self:
        assert isinstance(data, dict)
        result = super().model_validate(data)
        nodes_load_map = {i: o for i, o in result._nodes_map()}
        for field, graph in result.all_graphs().items():
            input = TypeAdapter(dict[str, list[str]]).validate_python(data[field])
            nx.relabel_nodes(
                nx.from_dict_of_lists(input, graph), nodes_load_map, copy=False
            )
        return result

    @classmethod
    def model_validate_json(cls, json: str) -> Self:
        return cls.model_validate(loads(json))

    @classmethod
    def graph_fields(cls) -> list[str]:
        annotations: dict[str, type[object]] = get_type_hints(cls)
        return [
            field
            for field, annotation in annotations.items()
            if issubclass(annotation, Graph)
        ]

    def all_graphs(self) -> dict[str, Graph[T]]:
        return {field: getattr(self, field) for field in self.graph_fields()}

    def model_dump_json(self) -> str:
        return dumps(self.model_dump())

    def dump(self, file: str):
        with open(file, "wt") as f:
            dump(self.model_dump(), f)

    @abstractmethod
    def _nodes_map(self) -> list[tuple[str, T]]:
        ...

    @override
    def _dump_field[V](self, field_name: str, annotation: type[V], data: V) -> object:
        nodes_dump_map = {o: i for i, o in self._nodes_map()}
        if isinstance(data, Graph):
            return nx.to_dict_of_lists(nx.relabel_nodes(data, nodes_dump_map))
        else:
            return TypeAdapter(annotation).dump_python(data, mode="json")

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
        if issubclass(annotation, Graph):
            return annotation()
        else:
            return TypeAdapter(annotation).validate_python(data)


@dataclass
class UserGraphOverlay(GraphOverlay[User]):
    users: list[User]

    @override
    def _nodes_map(self) -> list[tuple[str, User]]:
        return [(user.username, user) for user in self.users]


@dataclass
class Data(UserGraphOverlay):
    following: DiGraph[User]
