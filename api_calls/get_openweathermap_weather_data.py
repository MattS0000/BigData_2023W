import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from retarder import Retarder
from tqdm import tqdm

# ---

START_DATE = "2023-07-01"
END_DATE = "2023-09-30"
UTC_OFFSET = 2

VARIABLES = {
    "main": ["temp", "feels_like", "pressure", "humidity"],
    "wind": ["speed", "deg"],
    "clouds": ["all"],
    "rain": ["1h"],
    "snow": ["1h"],
}

API_TOKEN = ""
REQUEST_DELAY = 1

# ---

request_retarder = Retarder(REQUEST_DELAY)
expected_index = pd.date_range(
    datetime.fromisoformat(f"{START_DATE}T00:00:00{UTC_OFFSET:+03d}").astimezone(
        timezone.utc
    ),
    datetime.fromisoformat(f"{END_DATE}T23:00:00{UTC_OFFSET:+03d}").astimezone(
        timezone.utc
    ),
    freq="1H",
)


def get_response(latitude, longitude, start_timestamp, end_timestamp):
    request_retarder.step()
    response = requests.get(
        "https://history.openweathermap.org/data/2.5/history/city",
        {
            "lat": latitude,
            "lon": longitude,
            "start": start_timestamp,
            "end": end_timestamp,
            "type": "hour",
            "units": "metric",
            "appid": API_TOKEN,
        },
    ).json()
    return response


def split_into_weeks(start_date, end_date, utc_offset):
    start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00{utc_offset:+03d}")
    end_datetime = datetime.fromisoformat(f"{end_date}T23:00:00{utc_offset:+03d}")
    current_datetime = start_datetime
    while current_datetime <= end_datetime:
        yield (
            int(current_datetime.timestamp()),
            int(
                min(
                    current_datetime + timedelta(weeks=1, hours=-1), end_datetime
                ).timestamp()
            ),
        )
        current_datetime += timedelta(weeks=1)


def get_data(latitude, longitude):
    responses = [
        get_response(latitude, longitude, start_timestamp, end_timestamp)
        for start_timestamp, end_timestamp in split_into_weeks(
            START_DATE, END_DATE, UTC_OFFSET
        )
    ]
    data = pd.DataFrame(
        [
            {"time": item["dt"]}
            | {
                f"{group}_{name}": item.get(group, {}).get(name, 0)
                for group, names in VARIABLES.items()
                for name in names
            }
            for response in responses
            for item in response["list"]
        ]
    )
    data["time"] = pd.to_datetime(data["time"], utc=True, unit="s")
    data = (
        pd.DataFrame(index=expected_index)
        .join(data.set_index("time"))
        .reset_index(names="datetime")
    )
    return data


with open("./data/gios_stations.json") as fp:
    stations = json.load(fp)

for station in tqdm(stations):
    station_id = station["Identyfikator stacji"]
    latitude = station["WGS84 φ N"]
    longitude = station["WGS84 λ E"]
    data = get_data(latitude, longitude)
    data.to_csv(
        f"./data/weather/openweathermap/{station_id}.csv",
        date_format="%Y-%m-%dT%H:%M:%SZ",
        index=False,
        mode="x",
    )
