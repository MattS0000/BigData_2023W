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
    "co",
    "no",
    "no2",
    "o3",
    "so2",
    "pm2_5",
    "pm10",
    "nh3",
]

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


def get_data(latitude, longitude):
    request_retarder.step()
    response = requests.get(
        "http://api.openweathermap.org/data/2.5/air_pollution/history",
        {
            "lat": latitude,
            "lon": longitude,
            "start": int(
                datetime.fromisoformat(
                    f"{START_DATE}T00:00:00{UTC_OFFSET:+03d}"
                ).timestamp()
            ),
            "end": int(
                datetime.fromisoformat(
                    f"{END_DATE}T00:00:00{UTC_OFFSET:+03d}"
                ).timestamp()
            ),
            "appid": API_TOKEN,
        },
    ).json()
    data = pd.DataFrame(
        [
            {"time": item["dt"]}
            | {
                key: value
                for key, value in item["components"].items()
                if key in VARIABLES
            }
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
        f"./data/air/openweathermap/{station_id}.csv",
        date_format="%Y-%m-%dT%H:%M:%SZ",
        index=False,
        mode="x",
    )
