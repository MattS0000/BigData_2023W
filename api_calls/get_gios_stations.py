import json

import requests
from retarder import Retarder
from tqdm import tqdm

# ---

REQUEST_DELAY = 1

# ---

request_retarder = Retarder(REQUEST_DELAY)


def get_stations():
    response = requests.get(
        "https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll",
        {"size": 500},
    ).json()
    assert response["totalPages"] == 1
    data = response["Lista stacji pomiarowych"]
    return data


def get_sensors(station_id):
    request_retarder.step()
    response = requests.get(
        f"https://api.gios.gov.pl/pjp-api/v1/rest/station/sensors/{station_id}",
        {"size": 500},
    ).json()
    assert response["totalPages"] == 1
    data = response["Lista stanowisk pomiarowych dla podanej stacji"]
    return data


stations = get_stations()
for station in tqdm(stations):
    station_id = station["Identyfikator stacji"]
    station["Lista stanowisk pomiarowych"] = get_sensors(station_id)

with open("./data/gios_stations.json", "x") as fp:
    json.dump(stations, fp, ensure_ascii=False, indent=4)