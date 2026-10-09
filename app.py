from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
import json

import services

@asynccontextmanager
async def lifespan(app: FastAPI):
    services.initialise_database()

    with open("static/uk-train-stations.json") as file:
        data = file.read()

    json_data = json.loads(data)
    app.state.station_codes = [entry["station_code"] for entry in json_data]
    yield
    services.clear_cache()
    app.state.station_codes.clear()

app = FastAPI(lifespan=lifespan)

def get_station_codes_list(request: Request) -> list[str]:
    return request.app.state.station_codes

@app.get("/api/v1/delays/{station_code}")
def get_station_information(station_code: str, station_codes: list[str] = Depends(get_station_codes_list)):
    station_code = station_code.upper()

    if station_code not in station_codes:
        return {"success": False, "reason": "Invalid station code.", "response": None}

    cached_response = services.check_cache(station_code)

    if cached_response is not None:
        return {"success": True, "reason": None, "response": cached_response}
    else:
        response = services.get_station_delay_data(station_code)

        if response is None:
            return {"success": False, "reason": "Could not get station data.", "response": None}

        services.cache_result(station_code, json.dumps(response))

        return {"success": True, "reason": None, "response": response}

app.mount("/", StaticFiles(directory="static", html=True), name="static")