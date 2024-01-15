gcloud config set project favorable-bison-410912
gcloud functions deploy airQualityEndpoint --region=europe-central2 --runtime=nodejs18 --source=$(realpath ~/preingestion/) --entry-point=airQuality --trigger-http --memory=128MB
gcloud functions deploy openMeteoEndpoint --region=europe-central2 --runtime=nodejs18 --source=$(realpath ~/preingestion/) --entry-point=openMeteo --trigger-http --memory=128MB
gcloud functions deploy openWeatherMapEndpoint --region=europe-central2 --runtime=nodejs18 --source=$(realpath ~/preingestion/) --entry-point=openWeatherMap --trigger-http --memory=128MB