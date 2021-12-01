from typing import List, Dict

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import TextClause

from db.exceptions import RecordNotFound


def _sql_stmt_vehicle_data(vehicle_id: int) -> TextClause:
    return text(
        "with RECURSIVE "
        "    group_hierarchy AS ( "
        "        SELECT id, name, group_id, 0 AS relative_depth, f.id as feature_id "
        "        FROM feature f "
        f"        where id = ANY (select feature_id from vehicle_feature where vehicle_id = {vehicle_id}) "
        "        UNION ALL "
        "        SELECT g.id, g.name, g.group_id, gh.relative_depth - 1, gh.feature_id as feature_id "
        '        FROM "group" g, '
        "             group_hierarchy gh "
        "        WHERE g.id = gh.group_id "
        "    ), "
        "    feature_with_hierarchy AS ( "
        "        SELECT feature_id, array_agg((h.id, h.name)) as hierarchy "
        "        FROM group_hierarchy h "
        "        group by feature_id "
        "    ) "
        "select fwh.feature_id, fwh.hierarchy, array_agg((f.id, f.name)) as functions "
        "from feature_with_hierarchy fwh "
        "         join function f on fwh.feature_id = f.feature_id "
        "group by fwh.feature_id, fwh.hierarchy; "
    )


def _build_tree(dict_tree: dict, hierarchy: list, pointer: int = -1) -> dict:
    id, name = hierarchy[pointer][:2]
    if id not in dict_tree:
        dict_tree[id] = {"name": name, "subgroup": {}, "features": {}}

    if -pointer == len(hierarchy) - 1:
        feature_id, feature_name = hierarchy[0]
        dict_tree[id]["features"].update({feature_id: {"name": feature_name}})
        return dict_tree[id]["features"][feature_id]

    return _build_tree(dict_tree[id]["subgroup"], hierarchy, pointer - 1)


async def _get_vehicle_raw_tuples(session: AsyncEngine, vehicle_id: id) -> List[Row]:
    vehicle_result = await session.execute(_sql_stmt_vehicle_data(vehicle_id))
    raw_tuples = vehicle_result.fetchall()
    if not raw_tuples:
        raise RecordNotFound(f"Vehicle with id: {vehicle_id} does not exists")
    return raw_tuples


async def get_vehicle(engine: AsyncEngine, vehicle_id: id) -> dict:
    raw_tuples = await _get_vehicle_raw_tuples(engine, vehicle_id)
    dict_tree = {}
    for feature_id, hierarchy, functions in raw_tuples:
        s = _build_tree(dict_tree, hierarchy)

        s["functions"] = {}
        for func_id, func_name in functions:
            s["functions"].update({func_id: {"name": func_name}})

    return dict_tree
