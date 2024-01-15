import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.mongodbio import WriteToMongoDB
from apache_beam import window
import json
from google.cloud import storage
import pickle
from sklearn import linear_model
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
import time

project = 'favorable-bison-410912'
AirQualitySub = 'AirQualityTopic-sub'
OpenMeteoSub = 'OpenMeteoTopic-sub'
OpenWeatherSub = 'OpenWeatherMapTopic-sub'
meteo_labels=["lang","long",'temperature_2m','relativehumidity_2m','apparent_temperature','rain','pressure_msl','cloudcover','windspeed_10m', 'winddirection_10m']
air_labels=['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
coef_keys = [gas+"_"+feature for gas in air_labels for feature in meteo_labels+air_labels if gas!=feature]

# Initialise a client
def download_stations():
    storage_client = storage.Client(project)
    bucket = storage_client.get_bucket("bd_dataflow_output2")
    blob = bucket.blob("gios_stations.json")
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
SIZE=10

def delete_tiemstamp(element:dict):
    element.pop("timestamp",None)
    return element

def training_predictions(X,Y, X2pred):
    start=time.time()
    all_preds=[]
    coefs=[]
    for i in range(10,18):
        result,coef=train_model(X[:,list(range(0,i))+list(range(i+1,len(X[0])))],Y[:,i],X2pred[:,list(range(0,i))+list(range(i+1,len(X[0])))])
        print(coef.shape)
        coefs.append(coef)
        all_preds.append(result)
    print("Time:"+str(time.time()-start))
    return np.array(all_preds).transpose(),np.concatenate(coefs,axis=1)


def train_model(x, y, X2pred):
  REGRESSION.fit(x,y)
  return REGRESSION.predict(X2pred),np.repeat([REGRESSION.coef_],287,axis=0)

def per_station(data_tuple):
    combined=[]
    meteo, air = data_tuple
    if len(meteo)!=0 and len(air)!=0:
        for k in list(meteo[0].keys()):
            if k!="timestamp":
                columns=["N","E",*meteo[0][k],*air[0][k]]
                # print(columns)
                # print([k,*(stations[int(k[1:])]),*(meteo[0][k].values()),*(air[0][k].values())])
                tmp=list(meteo[0][k].values())
                combined.append([k[1:],meteo[0]["timestamp"],*(stations[int(k[1:])]),*(tmp[:4]+tmp[5:]),*(air[0][k].values())])
        
    return combined

def fill_and_train(element,GLOBAL,INDEXER):
    tmp_timestamp=np.array(element)[:,1].astype(float)
    tmp_stations=np.array(element)[:,0]
    element=np.array(element)[:,2:].astype(float)

    if len(GLOBAL)<SIZE:
        GLOBAL.append(element)
        return []
    
    GLOBAL[INDEXER[0]]=element
    
    Xidx = np.array(list(range(0,INDEXER[0]))+list(range(INDEXER[0]+1,SIZE)))
    Yidx = (Xidx+1)%SIZE
    X_train = np.concatenate(np.array(GLOBAL)[Xidx],axis=0)
    Y = np.concatenate(np.array(GLOBAL)[Yidx],axis=0)
    X2pred = np.array(GLOBAL[INDEXER[0]])
    predictions, coefs = training_predictions(X_train, Y, X2pred)
    print(coefs.shape)
    INDEXER[0]+=1
    if INDEXER[0]==SIZE:
        INDEXER[0]=0

    result=[]
    for i in range(287):
        meteo = {k:v for k,v in zip(meteo_labels,element[i][0:len(meteo_labels)])}
        airOriginal = {k+"Original":v for k,v in zip(air_labels,element[i][len(meteo_labels):])}
        airPred = {k+"Prediction":v for k,v in zip(air_labels,predictions[i])}

        
        coef_dict = {k:v for k,v in zip(coef_keys,coefs[i])}

        result_dict={"station":tmp_stations[i],"timestamp":tmp_timestamp[0]}
        result_dict.update(meteo)
        result_dict.update(airOriginal)
        result_dict.update(airPred)
        result_dict.update(coef_dict)
        result.append(result_dict)
        

    return result

class SplitRecords(beam.DoFn):
    def process(self, records):
        for record in records:
            yield record

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
        | beam.ParDo(SplitRecords())
        | WriteToMongoDB("mongodb://34.116.132.80:27017",db='test',coll='final2')
    )