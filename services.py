import requests
import datetime
import sqlite3
import json
import urllib.parse
from zoneinfo import ZoneInfo
from settings import TRANSPORTAPI_APP_ID, TRANSPORTAPI_APP_KEY

def convert_departure_to_datetime(time: dict) -> datetime.datetime:
    """ Convert departure date and time into a Python datetime object """
    if time is None:
        return None

    return datetime.datetime.strptime(f"{time['date']} {time['time']}", "%Y-%m-%d %H:%M")

def get_station_delay_data(station: str) -> dict:
    """ Grabs the station delays/cancellation data using TransportAPI and parses the data ready for the frontend. """

    try:
        zone = ZoneInfo("Europe/London")
        date_time = datetime.datetime.now(zone).replace(microsecond=0).isoformat()
        date_time = urllib.parse.quote_plus(date_time)

        api_url = f"https://transportapi.com/v3/uk/train/station_actual_journeys/crs:{station}.json?app_id={TRANSPORTAPI_APP_ID}&app_key={TRANSPORTAPI_APP_KEY}&datetime={date_time}&expected=true&limit=10&page=1"

        result = requests.get(url=api_url, timeout=15)
        result.raise_for_status()

        response = result.json()

        member = response.get("member")

        if member is None:
            return None

        data = []

        for item in member:
            service = item.get("service", {})

            cancellation = service.get("cancellation") or {}
            running_late = service.get("running_late") or {}

            aimed = item.get("aimed") or {}
            actual = item.get("actual") or {}
            expected = item.get("expected") or {}

            data_dict = {
                "operator": service.get("toc", {}).get("name"),
                "origin": service.get("origin_name"),
                "destination": service.get("destination_name"),
                "platform": item.get("platform"),
                "cancelled": item.get("cancelled", False),
            }

            if item.get("cancelled"):
                data_dict.update({
                    "status": "cancelled",
                    "reason": cancellation.get("reason"),
                    "reached_station": False,
                    "scheduled_time": None,
                    "actual_time": None,
                    "expected_time": None,
                    "delay_minutes": None,
                })

                data.append(data_dict)
                continue

            stop_type = item.get("stop_type")

            if stop_type == "OR":
                movement_type = "departure"
            else:
                movement_type = "arrival"

            aimed_time_data = aimed.get(movement_type)
            actual_time_data = actual.get(movement_type)
            expected_time_data = expected.get(movement_type)

            aimed_time = convert_departure_to_datetime(aimed_time_data)
            actual_time = convert_departure_to_datetime(actual_time_data)
            expected_time = convert_departure_to_datetime(expected_time_data)

            if actual_time is not None:
                delay_minutes = None

                if aimed_time is not None:
                    delay_minutes = round((actual_time - aimed_time).total_seconds() / 60)

                data_dict.update({
                    "status": "arrived" if movement_type == "arrival" else "departed",
                    "reached_station": True,
                    "scheduled_time": aimed_time_data.get("time") if aimed_time_data else None,
                    "actual_time": actual_time_data.get("time"),
                    "expected_time": expected_time_data.get("time") if expected_time_data else None,
                    "delay_minutes": delay_minutes,
                    "reason": running_late.get("reason") if delay_minutes and delay_minutes > 0 else None
                })

            else:
                delay_minutes = None

                if aimed_time is not None and expected_time is not None:
                    delay_minutes = round((expected_time - aimed_time).total_seconds() / 60)

                data_dict.update({
                    "status": "expected",
                    "reached_station": False,
                    "scheduled_time": aimed_time_data.get("time") if aimed_time_data else None,
                    "actual_time": None,
                    "expected_time": expected_time_data.get("time") if expected_time_data else None,
                    "delay_minutes": delay_minutes,
                    "reason": running_late.get("reason") if delay_minutes and delay_minutes > 0 else None
                })

            data.append(data_dict)

        return {
            "station": {
                "name": response.get("station_name"),
                "code": response.get("station_code"),
            },
            "updated_at": response.get("request_time"),
            "services": data,
        }

    except (requests.exceptions.HTTPError, requests.exceptions.RequestException):
        print("An error has occured while the data was being fetched. Please try again later.")
        return None
    except requests.exceptions.JSONDecodeError:
        print("Could not decode the response from the API. Please try again later.")
        return None
    except Exception as err:
        print("An error has occured:", err)
        return None

def initialise_database() -> None:
    """ Creates the cache database and sets up the tables if they don't already exist. """

    try:
        db = sqlite3.connect("cache.db")
        cursor = db.cursor()

        CREATE_CACHE_TABLE_QUERY = "CREATE TABLE IF NOT EXISTS cache (" \
        "station_code TEXT PRIMARY KEY NOT NULL," \
        "response TEXT NOT NULL," \
        "last_updated TEXT DEFAULT CURRENT_TIMESTAMP" \
        ");"

        cursor.execute(CREATE_CACHE_TABLE_QUERY)
        db.commit()
        db.close()

    except sqlite3.Error:
        raise Exception("Cache database could not be initialised.")

def cache_result(station_code: str, response) -> None:
    """ Add the cached result into the cache database. """

    try:
        db = sqlite3.connect("cache.db")
        cursor = db.cursor()

        CACHE_QUERY = "INSERT INTO cache (station_code, response) VALUES (?, ?) ON CONFLICT(station_code) DO UPDATE SET response = ?, last_updated = CURRENT_TIMESTAMP;"
        cursor.execute(CACHE_QUERY, (station_code, response, response))

        db.commit()
        db.close()

    except sqlite3.Error:
        print("Could not cache response.")

def check_cache(station_code: str) -> str | None:
    """ Check if the response for the given station code has already been cached in the database. """

    try:
        db = sqlite3.connect("cache.db")
        cursor = db.cursor()

        cutoff_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, microsecond=0) - datetime.timedelta(minutes=10)

        GET_CACHE_QUERY = "SELECT response FROM cache WHERE station_code = ? AND last_updated > ?"
        cached_result = cursor.execute(GET_CACHE_QUERY, (station_code, cutoff_time)).fetchone()

        db.close()

        return json.loads(cached_result[0]) if cached_result else None
    
    except sqlite3.Error:
        print("Could not get cached response.")

def clear_cache() -> None:
    """ Clear the cache database upon program exit. """

    try:
        db = sqlite3.connect("cache.db")
        cursor = db.cursor()

        cursor.execute("DELETE FROM cache")

        db.commit()
        db.close()
        
    except sqlite3.Error:
        print("Could not clear cache.")