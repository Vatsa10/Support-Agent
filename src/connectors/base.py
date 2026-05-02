from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Type


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters_schema: dict = field(default_factory=dict)
    kind: str = ""  # connector kind that owns this tool


class Connector(ABC):
    kind: str = ""

    def __init__(self, creds: dict, config: dict):
        self.creds = creds or {}
        self.config = config or {}

    @abstractmethod
    def tool_specs(self) -> list[ToolSpec]: ...

    @abstractmethod
    async def execute(self, tool_name: str, args: dict) -> dict: ...


KIND_TO_CLASS: dict[str, Type[Connector]] = {}


def register(cls: Type[Connector]) -> Type[Connector]:
    if not cls.kind:
        raise ValueError(f"{cls.__name__} missing 'kind'")
    KIND_TO_CLASS[cls.kind] = cls
    return cls


def load_connector(kind: str, creds: dict, config: dict) -> Connector:
    if kind not in KIND_TO_CLASS:
        raise ValueError(f"Unknown connector kind: {kind}")
    return KIND_TO_CLASS[kind](creds, config)
