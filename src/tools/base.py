from typing import Callable, List, Optional
from pydantic import BaseModel
import json


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict

    class Config:
        extra = "forbid"


class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def to_openai_format(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }


def create_tool(name: str, description: str, parameters: dict = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        func._tool_name = name
        func._tool_description = description
        func._tool_parameters = parameters or {}
        return func

    return decorator


class ToolRegistry:
    def __init__(self):
        self._tools: List[Tool] = []

    def register(self, tool: Tool):
        self._tools.append(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None

    def get_all_tools(self) -> List[Tool]:
        return self._tools

    def get_openai_tools(self) -> List[dict]:
        return [tool.to_openai_format() for tool in self._tools]


tool_registry = ToolRegistry()
