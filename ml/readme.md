## Setup
An authentication key is required to run the container. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts/details/106893458450976419299/keys?authuser=2&walkthrough_id=iam--create-service-account-keys&project=gcc2023-385607&supportedpurview=project), then generate a key by going `Add key` -> `Create new key`. Move the downloaded file in this folder and rename it to `gcc-key.json`.

## Running
To restart the container with rebuilding from source files, execute:

```
docker compose down
docker compose build
docker compose up
```

To restart without rebuilding, execute:
```
docker compose up
```