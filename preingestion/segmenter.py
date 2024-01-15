import pandas as pd
import os
import json
from collections import defaultdict

paths = ["air/openweathermap", "weather/openmeteo", "weather/openweathermap"]
files = os.listdir(paths[0])

for path in paths:
    aggregate = defaultdict(dict)
    for file in files:
        df = pd.read_csv(f"data/{path}/{file}")
        df = df.dropna()

        for index, row in df.iterrows():
            row_dict = row.to_dict()
            del row_dict["datetime"]
            aggregate[index][file.split(".")[0]] = row_dict
    
    for index, row in aggregate.items():
        if not os.path.exists(f"data/segmented/{path}"):
            os.makedirs(f"data/segmented/{path}")
        f = open(f"data/segmented/{path}/{index}.json", "w")
        f.write(json.dumps(row))
        f.close()