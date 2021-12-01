from aiohttp import web

from db.exceptions import RecordNotFound
from db.queries.vehicle import get_vehicle
from exceptions import JsonHTTPNotFound

routes = web.RouteTableDef()


@routes.get('/vehicle/{id}')
async def vehicle(request):
    """Retrieve data about a particular vehicle."""
    vehicle_id = int(request.match_info['id'])
    try:
        vehicle = await get_vehicle(request["db_session"], vehicle_id)
    except RecordNotFound as e:
        raise JsonHTTPNotFound(text=str(e))

    return web.json_response(vehicle.dict())