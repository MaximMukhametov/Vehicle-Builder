from __future__ import annotations

from typing import List, Dict

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.elements import TextClause

from db.exceptions import RecordNotFound
from db.models import Vehicle


def _sql_stmt_vehicle_data(features: List[int]) -> TextClause:
    """SQL statement for getting hierarchy list of groups, features, and functions related to all features."""
    return text(
        "with RECURSIVE "
        "    group_hierarchy AS ( "
        "        SELECT id, name, False AS is_set, group_id, 0 AS relative_depth, f.id as feature_id "
        "        FROM feature f "
        f"        where id = ANY (ARRAY{features}) "
        "        UNION ALL "
        "        SELECT g.id, g.name, g.is_set, g.group_id, gh.relative_depth - 1, gh.feature_id as feature_id "
        '        FROM "group" g, '
        "             group_hierarchy gh "
        "        WHERE g.id = gh.group_id "
        "    ), "
        "    feature_with_hierarchy AS ( "
        "        SELECT feature_id, array_agg((h.id, h.name, h.is_set)) as hierarchy "
        "        FROM group_hierarchy h "
        "        group by feature_id "
        "    ) "
        "select fwh.feature_id, fwh.hierarchy, array_agg((f.id, f.name)) as functions "
        "from feature_with_hierarchy fwh "
        "         join function f on fwh.feature_id = f.feature_id "
        "group by fwh.feature_id, fwh.hierarchy; "
    )


class RootGroupModel(BaseModel):
    name: str = "Root Group"
    groups: Dict[int, GroupModel] = dict()


class FunctionModel(BaseModel):
    name: str


class FeatureModel(BaseModel):
    name: str
    functions: Dict[int, FunctionModel] = dict()


class GroupModel(BaseModel):
    name: str
    is_set: bool
    subgroups: Dict[int, GroupModel] = dict()
    features: Dict[int, FeatureModel] = dict()


class VehicleModel(BaseModel):
    id: int
    name: str
    range: int
    features: RootGroupModel = RootGroupModel()


def _build_tree(node: dict, hierarchy: List[int], pointer: int = -1) -> FeatureModel:
    """Build a tree of Groups, Features according to hierarchy list."""
    id, name, is_set = hierarchy[pointer][:3]
    if id not in node:
        node[id] = GroupModel(name=name, is_set=is_set)

    if -pointer == len(hierarchy) - 1:
        feature_id, feature_name, _ = hierarchy[0]
        feature = FeatureModel(name=feature_name)
        node[id].features.update({feature_id: feature})
        return feature

    return _build_tree(node[id].subgroups, hierarchy, pointer - 1)


async def _get_vehicle_raw_tuples(session: AsyncSession, features: List[int]) -> List[Row]:
    """Get raw tuples with hierarchy list of groups, features, and functions related to all features.

    Example:
        feature_id | hierarchy | functions
        2 | {"(1,Feature2)","(4,Group3)","(3,Group2)","(1,Group1)"} | {""(2,Function1)"",""(3,Function2)""}

    """
    vehicle_result = await session.execute(_sql_stmt_vehicle_data(features))
    return vehicle_result.fetchall()


async def get_vehicle_features(session: AsyncSession, features: List[int]) -> RootGroupModel:
    """Get a tree of Groups, Features and Functions for by Vehicle."""
    raw_tuples = await _get_vehicle_raw_tuples(session, features)
    root = RootGroupModel()
    for _, hierarchy, functions in raw_tuples:
        feature = _build_tree(node=root.groups, hierarchy=hierarchy)

        # set all functions related to the feature
        for func_id, func_name in functions:
            feature.functions.update({func_id: FunctionModel(name=func_name)})

    return root


async def get_vehicle(session: AsyncSession, vehicle_id: id) -> VehicleModel:
    """Get vehicle from db."""
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id).options(joinedload(Vehicle.features))
    result = await session.execute(stmt)
    vehicle = result.scalars().first()

    if not vehicle:
        raise RecordNotFound(f"Vehicle with id: {vehicle_id} does not exists")

    vehicle_data = vehicle.to_dict()
    if features := [f.id for f in vehicle.features]:
        vehicle_data["features"] = await get_vehicle_features(session, features)

    return VehicleModel(**vehicle_data)
