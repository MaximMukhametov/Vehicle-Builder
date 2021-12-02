from __future__ import annotations

from typing import Dict

from pydantic import BaseModel


class FunctionModel(BaseModel):
    id: int
    name: str


class FeatureModel(BaseModel):
    id: int
    name: str
    functions: Dict[int, FunctionModel] = dict()


class GroupModel(BaseModel):
    id: int
    name: str
    is_set: bool
    subgroups: Dict[int, GroupModel] = dict()
    features: Dict[int, FeatureModel] = dict()


class VehicleModel(BaseModel):
    id: int
    name: str
    range: int
    groups: Dict[int, GroupModel] = dict()
