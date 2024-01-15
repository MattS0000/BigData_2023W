import json
from datetime import datetime, timezone

import pandas as pd
import requests
from retarder import Retarder
from tqdm import tqdm

# ---

START_DATE = "2023-07-01"
END_DATE = "2023-09-30"
UTC_OFFSET = 2

VARIABLES = [
    "temperature_2m",
    "relativehumidity_2m",
    "apparent_temperature",
    "rain",
    "snowfall",
    "pressure_msl",
    "cloudcover",
    "windspeed_10m",
    "winddirection_10m",
]

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


def get_data(latitude, longitude):
    request_retarder.step()
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "hourly": ",".join(VARIABLES),
            "timezone": f"Etc/GMT{-UTC_OFFSET:+d}",
        },
    ).json()
    data = pd.DataFrame(response["hourly"])
    data["time"] = pd.to_datetime(data["time"] + f"{UTC_OFFSET:+03d}:00", utc=True)
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
        f"./data/weather/openmeteo/{station_id}.csv",
        date_format="%Y-%m-%dT%H:%M:%SZ",
        index=False,
        mode="x",
    )