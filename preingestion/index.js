const functions = require('@google-cloud/functions-framework');
const {Storage} = require('@google-cloud/storage');
const gcs = new Storage();
const bucket = gcs.bucket("endpointdata2");

const maxFile = 2185
function getData(req, res, path) {
    res.set('Access-Control-Allow-Origin', '*');
  
    if (req.method === 'OPTIONS') {
      res.set('Access-Control-Allow-Methods', 'GET');
      res.set('Access-Control-Allow-Headers', 'Content-Type');
      res.set('Access-Control-Max-Age', '3600');
      res.status(204).send('');
    } else {
        let current = Math.floor(Date.now()/10000)%(maxFile*2-2)
        if(current >= maxFile) current = maxFile*2-current-2

        const file = bucket.file(path+current+".json")
        file.download((err, content) => {
            res.send(content.toString());
        })
    }
}

functions.http('airQuality', (req, res) => {getData(req, res, "air/openweathermap/")});
functions.http('openMeteo', (req, res) => {getData(req, res, "weather/openmeteo/")});
functions.http('openWeatherMap', (req, res) => {getData(req, res, "weather/openweathermap/")});