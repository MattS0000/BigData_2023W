import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam import window
import json
from google.cloud import storage
import pickle
from sklearn import linear_model
import numpy as np
import pandas as pd

project = 'gcc2023-385607'
AirQualitySub = 'AirQualityTopic-sub'
OpenMeteoSub = 'OpenMeteoTopic-sub'
OpenWeatherSub = 'OpenWeatherMapTopic-sub'


# Initialise a client
def download_stations():
    storage_client = storage.Client(project)
    # Create a bucket object for our bucket
    bucket = storage_client.get_bucket("bd_dataflow_output")
    # Create a blob object from the filepath
    blob = bucket.blob("gios_stations.json")
    # Download the file to a destination
    blob.download_to_filename("./gios_stations.json")
download_stations()
with open("gios_stations.json","r",encoding="utf-8") as f:
    stations_json=json.load(f)
stations={}
for i in stations_json:
    stations[i["Identyfikator stacji"]]=(float(i["WGS84 φ N"]),float(i["WGS84 λ E"]))

options = PipelineOptions()
google_cloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
google_cloud_options.project = project
options.view_as(StandardOptions).streaming = True
options.view_as(SetupOptions).save_main_session = True

GLOBAL=[]
INDEXER = [0]
REGRESSION = linear_model.LinearRegression()

def delete_tiemstamp(element:dict):
    element.pop("timestamp",None)
    return element

def train_model(x, y):
  REGRESSION.fit(x,y)

def per_station(data_tuple):
    combined=[]
    meteo, air = data_tuple
    if len(meteo)!=0 and len(air)!=0:
        for k in list(meteo[0].keys()):
            if k!="timestamp":
                columns=["N","E",*meteo[0][k],*air[0][k]]
                # print(columns)
                # print([*(stations[int(k[1:])]),*(meteo[0][k].values()),*(air[0][k].values())])
                combined.append([*(stations[int(k[1:])]),*(meteo[0][k].values()),*(air[0][k].values())])
        
    return combined

def fill_and_train(element,GLOBAL,INDEXER):
    
    if len(GLOBAL)<5:
        print(INDEXER,len(GLOBAL))
        GLOBAL.append(element)
        return element
    
    GLOBAL[INDEXER[0]]=element
    INDEXER[0]+=1
    if INDEXER[0]==5:
        INDEXER[0]=0
    train_set=np.concatenate(GLOBAL,axis=0)
    print(train_set.shape)
    train_model(train_set[:,:-1],train_set[:,-1])
    return element



class ReturnNonEmpty(beam.DoFn):
    def process(self, element):
        if element!=[]:
            yield element

with beam.Pipeline(options=options) as pipeline:

    messagesMeteo = (
        pipeline
        | 'Read METEO from Pub/Sub' >> beam.io.gcp.pubsub.ReadFromPubSub(
            subscription=f"projects/{project}/subscriptions/{OpenMeteoSub}",
        ).with_output_types(bytes) 
        | 'Load messagesMeteo' >> beam.Map(json.loads)
        | 'Extract METEO Key-Value' >> beam.Map(lambda x:(int(str(x["timestamp"])[:-4]),x))
        | 'w1' >> beam.WindowInto(window.FixedWindows(10))
    )

    messagesAir = (
        pipeline
        | 'Read AIR from Pub/Sub' >> beam.io.gcp.pubsub.ReadFromPubSub(
            subscription=f"projects/{project}/subscriptions/{AirQualitySub}",).with_output_types(bytes) 
        | 'Load messagesAir' >> beam.Map(json.loads)
        | 'Extract AIR Key-Value' >> beam.Map(lambda x:(int(str(x["timestamp"])[:-4]),x))
        | 'w2' >> beam.WindowInto(window.FixedWindows(10))
    )
    result_pcoll = (
        {'messagesMeteo': messagesMeteo, 'messagesAir': messagesAir}
        | beam.CoGroupByKey()
        | beam.Map(lambda x: (x[1]["messagesMeteo"],x[1]["messagesAir"]))
        | beam.Map(lambda x: per_station(x))
        | beam.ParDo(ReturnNonEmpty())
        | beam.Map(lambda x: fill_and_train(x,GLOBAL,INDEXER))
    )