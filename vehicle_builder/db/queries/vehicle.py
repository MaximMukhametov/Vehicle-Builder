from typing import List, Dict, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.elements import TextClause

from db.exceptions import RecordNotFound
from db.models import Vehicle
from db.schemas import GroupModel, FeatureModel, FunctionModel, RootGroupModel, VehicleModel


def _sql_stmt_vehicle_data(features: List[int]) -> TextClause:
    """SQL statement for getting hierarchy list of groups, features, and functions related to all features."""
    return text(
        "with RECURSIVE "
        "    group_hierarchy AS ( "
        "        SELECT id, name, False AS is_set, group_id, f.id as feature_id "
        "        FROM feature f "
        f"        where id = ANY (ARRAY{features}) "
        "        UNION ALL "
        "        SELECT g.id, g.name, g.is_set, g.group_id, gh.feature_id "
        '        FROM "group" g, '
        "             group_hierarchy gh "
        "        WHERE g.id = gh.group_id "
        "    ), "
        "    feature_with_hierarchy AS ( "
        "        SELECT feature_id, array_agg((id, name, is_set)) as hierarchy "
        "        FROM group_hierarchy "
        "        group by feature_id "
        "    ) "
        "select fwh.feature_id, fwh.hierarchy, array_agg((f.id, f.name)) as functions "
        "from feature_with_hierarchy fwh "
        "         join function f on fwh.feature_id = f.feature_id "
        "group by fwh.feature_id, fwh.hierarchy; "
    )


def _build_tree(subgroups: Dict[int, GroupModel], hierarchy: List[int], functions: Tuple[int, str]) -> None:
    """Build a tree of Groups, Features, Functions according to hierarchy list."""
    last_group = None
    for group_id, group_name, is_set in hierarchy[:0:-1]:
        if group_id not in subgroups:
            subgroups[group_id] = GroupModel(id=group_id, name=group_name, is_set=is_set)
        last_group = subgroups[group_id]
        subgroups = subgroups[group_id].subgroups

    feature_id, feature_name, _ = hierarchy[0]
    feature = FeatureModel(id=feature_id, name=feature_name)
    last_group.features.update({feature_id: feature})

    # set all functions related to the feature
    for func_id, func_name in functions:
        feature.functions.update({func_id: FunctionModel(id=func_id, name=func_name)})


async def _get_vehicle_raw_tuples(session: AsyncSession, features: List[int]) -> List[Row]:
    """Get raw tuples with hierarchy list of groups, features, and functions related to all features.

    Example:
        (feature_id, hierarchy[(id, name, is_set)], functions[(id, name)])
        (1, [(1, 'Feature2', False), (3, 'Group2', True), (1, 'Group1', False)], [(1, 'Function4')])

    """
    vehicle_result = await session.execute(_sql_stmt_vehicle_data(features))
    return vehicle_result.fetchall()


async def get_vehicle_features(session: AsyncSession, features: List[int]) -> RootGroupModel:
    """Get a tree of Groups, Features and Functions for by Vehicle."""
    raw_tuples = await _get_vehicle_raw_tuples(session, features)
    root = RootGroupModel()
    for _, hierarchy, functions in raw_tuples:
        _build_tree(subgroups=root.groups, hierarchy=hierarchy, functions=functions)

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
